#!/usr/bin/env python3
"""teller — a local storytelling agent for fragment-structured story repos.

Point it at this repository, or any repository with the same shape:

    scenes/fragment-NNN.md    one fragment per file: header, `---`, prose
    private-canon.md          a `## Log` of numbered rulings (optional)

and it walks you through the story as a paced, navigable adventure: prose
delivered a passage at a time, with the record available to consult as you go.

No dependencies, no network, no model — Python standard library only.
It invents nothing. Every word it shows you is a word the author wrote.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
import textwrap
from dataclasses import dataclass, field

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import questfile  # noqa: E402  (sibling module, stdlib-only)

PROGRESS_FILE = ".teller-progress.json"

TITLE_RE = re.compile(
    r"^#\s*Fragment\s+(\d+)\s*[—-]\s*(.+?)\s*\((APPROVED[^)]*|DRAFT)\)\s*$"
)
LOG_RE = re.compile(r"^###\s*(\d+)\s*[—-]\s*(\S+)\s*[—-]\s*(.+?)\s*$")
OPEN_RE = re.compile(
    r"(?:Still open after\s+ratification|Deliberately not\s+fixed)\s*:\s*(.+?)"
    r"(?:Tone rule|$)",
    re.S,
)


def term_width() -> int:
    return min(shutil.get_terminal_size((80, 24)).columns, 84)


def wrap(text: str, indent: str = "") -> str:
    body = " ".join(text.split())
    return textwrap.fill(
        body, width=term_width() - len(indent),
        initial_indent=indent, subsequent_indent=indent,
    )


def strip_md(text: str) -> str:
    return re.sub(r"\*\*|`|\*|\[|\]", "", text)


def first_point(body: str) -> str:
    """The whole of a log entry's first bullet, unwrapped and de-marked."""
    lines = body.splitlines()
    start = next((i for i, ln in enumerate(lines) if ln.lstrip().startswith("- ")), None)
    if start is None:
        return strip_md(" ".join(body.split())[:300])
    out = [lines[start].lstrip()[2:]]
    for ln in lines[start + 1:]:
        if ln.lstrip().startswith("- ") or not ln.strip():
            break
        out.append(ln.strip())
    text = strip_md(" ".join(" ".join(out).split()))
    return text if len(text) <= 320 else text[:317].rsplit(" ", 1)[0] + "…"


def dim(s: str) -> str:
    return f"\033[2m{s}\033[0m" if sys.stdout.isatty() else s


def bold(s: str) -> str:
    return f"\033[1m{s}\033[0m" if sys.stdout.isatty() else s


def read_progress(root: str) -> dict:
    try:
        with open(os.path.join(root, PROGRESS_FILE), encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return {}


def write_progress(root: str, **updates) -> None:
    d = read_progress(root)
    d.update(updates)
    try:
        with open(os.path.join(root, PROGRESS_FILE), "w", encoding="utf-8") as fh:
            json.dump(d, fh)
    except OSError:
        pass


@dataclass
class Fragment:
    number: int
    title: str
    status: str
    header: str
    passages: list[str] = field(default_factory=list)

    @property
    def approved(self) -> bool:
        return self.status.startswith("APPROVED")

    @property
    def label(self) -> str:
        mark = " " if self.approved else "*"
        return f"{mark}{self.number:03d}  {self.title}"

    def open_items(self) -> str | None:
        m = OPEN_RE.search(self.header)
        return strip_md(" ".join(m.group(1).split())).rstrip(". ") if m else None


@dataclass
class LogEntry:
    number: int
    date: str
    title: str
    body: str


def load_fragments(root: str) -> list[Fragment]:
    scenes = os.path.join(root, "scenes")
    if not os.path.isdir(scenes):
        return []
    out: list[Fragment] = []
    for name in sorted(os.listdir(scenes)):
        if not (name.startswith("fragment-") and name.endswith(".md")):
            continue
        with open(os.path.join(scenes, name), encoding="utf-8") as fh:
            lines = fh.read().splitlines()
        if not lines:
            continue
        m = TITLE_RE.match(lines[0])
        if not m:
            continue
        split = next((i for i, ln in enumerate(lines) if ln.strip() == "---"), None)
        header = "\n".join(lines[1:split]) if split else "\n".join(lines[1:])
        body = lines[split + 1:] if split else []
        passages, buf = [], []
        for ln in body:
            if ln.strip():
                buf.append(ln.strip())
            elif buf:
                passages.append(" ".join(buf))
                buf = []
        if buf:
            passages.append(" ".join(buf))
        out.append(Fragment(int(m.group(1)), m.group(2), m.group(3), header, passages))
    return out


def load_log(root: str) -> list[LogEntry]:
    path = os.path.join(root, "private-canon.md")
    if not os.path.isfile(path):
        return []
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    if "## Log" in text:
        text = text.split("## Log", 1)[1]
    entries: list[LogEntry] = []
    cur: LogEntry | None = None
    buf: list[str] = []
    for ln in text.splitlines():
        m = LOG_RE.match(ln)
        if m:
            if cur:
                cur.body = "\n".join(buf).strip()
                entries.append(cur)
            cur = LogEntry(int(m.group(1)), m.group(2), m.group(3), "")
            buf = []
        elif cur is not None:
            if ln.startswith("## "):
                break
            buf.append(ln)
    if cur:
        cur.body = "\n".join(buf).strip()
        entries.append(cur)
    return entries


HELP = """\
  [enter]   the next passage           o        what this fragment leaves open
  n / b     next / previous fragment   a WORD   ask the record about a word
  g N       go to fragment N           l        list fragments
  r         re-read this fragment      q        save and leave
"""


class Teller:
    def __init__(self, root: str, drafts: bool, pace: int) -> None:
        self.root = root
        self.pace = max(1, pace)
        allf = load_fragments(root)
        self.fragments = allf if drafts else [f for f in allf if f.approved]
        self.log = load_log(root)
        self.idx = 0
        self.pos = 0
        self._load_progress()

    # ---- progress -------------------------------------------------
    def _load_progress(self) -> None:
        d = read_progress(self.root)
        n = d.get("fragment")
        for i, f in enumerate(self.fragments):
            if f.number == n:
                self.idx, self.pos = i, int(d.get("passage", 0))
                break

    def save(self) -> None:
        if self.fragments:
            write_progress(self.root, fragment=self.current.number,
                           passage=self.pos)

    # ---- state ----------------------------------------------------
    @property
    def current(self) -> Fragment:
        return self.fragments[self.idx]

    def announce(self) -> None:
        f = self.current
        print()
        print(bold(f"Fragment {f.number:03d} — {f.title}"))
        tag = "ratified" if f.approved else "DRAFT — proposed, not canon"
        print(dim(f"  {tag} · {len(f.passages)} passages"))
        print()

    def go(self, i: int) -> None:
        self.idx = max(0, min(i, len(self.fragments) - 1))
        self.pos = 0
        self.announce()

    # ---- commands -------------------------------------------------
    def show_open(self) -> None:
        items = self.current.open_items()
        print()
        print(wrap("What this fragment leaves open: " + items if items
                   else "This fragment records nothing as left open.", "  "))
        print()

    def ask(self, term: str) -> None:
        term = term.strip().lower()
        if not term:
            print(dim("  ask what?"))
            return
        scored = []
        for e in self.log:
            hits = e.title.lower().count(term) * 8 + e.body.lower().count(term)
            if hits:
                scored.append((hits, e.number, e))
        scored.sort(reverse=True)
        print()
        if not scored:
            print(wrap(f"The record has nothing under “{term}”.", "  "))
            print()
            return
        n = len(scored)
        print(dim(f"  the record answers on “{term}” "
                  f"({n} entr{'y' if n == 1 else 'ies'}, closest first)"))
        for _, _, e in scored[:3]:
            print()
            print(wrap(f"{e.number:03d} — {e.date} — {e.title}", "  "))
            point = first_point(e.body)
            if point:
                print(wrap(point, "     "))
        if n > 3:
            print(dim(f"\n  …and {n - 3} more: "
                      + ", ".join(f"{e.number:03d}" for _, _, e in scored[3:9])))
        print()

    def listing(self) -> None:
        print()
        for i, f in enumerate(self.fragments):
            mark = "→" if i == self.idx else " "
            print(dim(f"  {mark} {f.label}"))
        print(dim("  * = draft"))
        print()

    # ---- loop -----------------------------------------------------
    def run(self) -> None:
        if not self.fragments:
            print(wrap("No fragments here. Reading mode expects "
                       "scenes/fragment-NNN.md files.", "  "))
            if questfile.find_quest(self.root):
                print(wrap("This repo does carry a quest file, though — "
                           "try --quest.", "  "))
            return
        print(bold("\n  the teller"))
        print(dim(wrap(f"{len(self.fragments)} fragments from {self.root}. "
                       "Press enter for the next passage; ? for help.", "  ")))
        self.announce()
        while True:
            while self.pos < len(self.current.passages):
                for _ in range(self.pace):
                    if self.pos >= len(self.current.passages):
                        break
                    print(wrap(self.current.passages[self.pos], "  "))
                    print()
                    self.pos += 1
                if self.pos >= len(self.current.passages):
                    break
                if not self.prompt(dim("  —")):
                    return
            if not self.end_of_fragment():
                return

    def end_of_fragment(self) -> bool:
        last = self.idx >= len(self.fragments) - 1
        print(dim("  ── end of fragment ──"))
        if last:
            print(dim(wrap("That is the whole record as it stands. "
                           "The rest is unruled page.", "  ")))
        return self.prompt(dim("  [enter] on" if not last else "  [enter]"),
                           at_end=True)

    def prompt(self, label: str, at_end: bool = False) -> bool:
        try:
            raw = input(label + " ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            self.save()
            return False
        cmd, _, arg = raw.partition(" ")
        cmd = cmd.lower()
        if cmd in ("q", "quit", "exit"):
            self.save()
            print(dim("  saved.\n"))
            return False
        if cmd in ("?", "h", "help"):
            print("\n" + HELP)
        elif cmd in ("o", "open"):
            self.show_open()
        elif cmd in ("a", "ask"):
            self.ask(arg)
        elif cmd in ("l", "list"):
            self.listing()
        elif cmd in ("r", "reread"):
            self.pos = 0
            self.announce()
        elif cmd in ("b", "back"):
            self.go(self.idx - 1)
        elif cmd in ("n", "next"):
            self.go(self.idx + 1)
        elif cmd in ("g", "go"):
            try:
                n = int(arg)
            except ValueError:
                print(dim("  go where? (g 12)"))
                return True
            match = next((i for i, f in enumerate(self.fragments)
                          if f.number == n), None)
            if match is None:
                print(dim(f"  no fragment {n} in play."))
            else:
                self.go(match)
        elif raw == "" and at_end:
            self.go(self.idx + 1)
        self.save()
        return True


QUEST_HELP = """\
  N         take that choice              x N      look at the Nth thing
  j         the quest log                 f        the companies present
  l         list chapters                 g N      go to chapter N
  r         restart this chapter          q        save and leave
"""


class QuestPlayer:
    """Plays the hand-authored chapters of a one-file quest engine."""

    def __init__(self, root: str, data: dict) -> None:
        self.root = root
        self.chapters = data["chapters"]
        self.examine = data["examine"]
        self.factions = data["factions"]
        self.chapter_factions = data["chapter_factions"]
        self.idx = 0
        self.beat = 0
        d = read_progress(root).get("quest") or {}
        for i, c in enumerate(self.chapters):
            if c.get("saveId") == d.get("saveId"):
                self.idx = i
                self.beat = int(d.get("beat", 0))
                break

    # ---- state ----------------------------------------------------
    @property
    def chapter(self) -> dict:
        return self.chapters[self.idx]

    @property
    def beats(self) -> list:
        return self.chapter.get("beats", [])

    def save(self) -> None:
        write_progress(self.root, quest={"saveId": self.chapter.get("saveId"),
                                         "beat": self.beat})

    def go(self, i: int) -> None:
        self.idx = max(0, min(i, len(self.chapters) - 1))
        self.beat = 0
        self.announce()

    def announce(self) -> None:
        c = self.chapter
        print()
        print(bold("  " + c.get("title", "")))
        if c.get("sub"):
            print(dim(wrap(c["sub"], "  ")))
        keys = self.chapter_factions.get(c.get("saveId"), [])
        names = [self.factions[k]["name"] for k in keys if k in self.factions]
        if names:
            print(dim(wrap("companies: " + " · ".join(names), "  ")))
        print()

    # ---- panels ---------------------------------------------------
    def quest_log(self) -> None:
        print()
        for i, b in enumerate(self.beats):
            if i > self.beat:
                break
            mark = "·" if i < self.beat else "→"
            print(dim(f"  {mark} {b.get('log', '')}"))
        held = self.chapter.get("heldLine")
        if held:
            print(dim(f"  · {held} (held)"))
        print()

    def companies(self) -> None:
        keys = self.chapter_factions.get(self.chapter.get("saveId"), [])
        print()
        if not keys:
            print(dim("  no companies stand behind this chapter."))
            print()
            return
        for k in keys:
            f = self.factions.get(k)
            if not f:
                continue
            print(wrap(f["name"], "  "))
            if f.get("of") and f["of"] in self.factions:
                print(wrap("Of " + self.factions[f["of"]]["name"] + ".", "     "))
            print(wrap("Seat: " + f.get("seat", "") + ".", "     "))
            print(wrap("Quest: " + f.get("quest", ""), "     "))
            for m in f.get("members", []):
                print(wrap(m + ".", "     "))
            print()

    def listing(self) -> None:
        print()
        for i, c in enumerate(self.chapters):
            mark = "→" if i == self.idx else " "
            print(dim(f"  {mark} {i + 1:2d}  {c.get('title', '')}"))
        print()

    def look(self, key: str) -> None:
        item = self.examine.get(key)
        print()
        if item:
            print(dim(wrap(item.get("text", ""), "  ")))
        else:
            print(dim("  nothing of that name here."))
        print()

    # ---- loop -----------------------------------------------------
    def run(self) -> None:
        if not self.chapters:
            print("No chapters found in the quest file.")
            return
        print(bold("\n  the teller — quest"))
        print(dim(wrap(f"{len(self.chapters)} chapters, "
                       f"{sum(len(c.get('beats', [])) for c in self.chapters)} "
                       "beats. Choices are the author's; ? for help.", "  ")))
        self.announce()
        while True:
            if self.beat >= len(self.beats):
                if not self.endcard():
                    return
                continue
            b = self.beats[self.beat]
            print(dim("  ── " + b.get("log", "") + " ──"))
            pres = b.get("presences") or []
            if pres:
                print(dim(wrap("present: " + " · ".join(pres), "  ")))
            print()
            for para in b.get("enter", []):
                print(wrap(para, "  "))
                print()
            if not self.offer(b):
                return

    def offer(self, beat: dict) -> bool:
        choices = beat.get("choices") or []
        looks = [k for k in (beat.get("examine") or []) if k in self.examine]
        while True:
            if choices:
                for i, c in enumerate(choices, 1):
                    print(wrap(f"{i}) {c.get('label', '')}", "  "))
            else:
                print(wrap("1) " + (beat.get("continueLabel") or "Go on."), "  "))
            if looks:
                items = " · ".join(
                    f"{i} {self.examine[k].get('label', k)}"
                    for i, k in enumerate(looks, 1))
                print(dim(wrap("look at: " + items + "   (x N)", "  ")))
            print()
            try:
                raw = input(dim("  > ")).strip()
            except (EOFError, KeyboardInterrupt):
                print()
                self.save()
                return False
            cmd, _, arg = raw.partition(" ")
            cmd = cmd.lower()
            if cmd in ("q", "quit", "exit"):
                self.save()
                print(dim("  saved.\n"))
                return False
            if cmd in ("?", "h", "help"):
                print("\n" + QUEST_HELP)
            elif cmd in ("j", "log"):
                self.quest_log()
            elif cmd in ("f", "companies"):
                self.companies()
            elif cmd in ("l", "list"):
                self.listing()
            elif cmd in ("r", "restart"):
                self.beat = 0
                self.announce()
                return True
            elif cmd in ("g", "go"):
                try:
                    self.go(int(arg) - 1)
                    return True
                except ValueError:
                    print(dim("  go where? (g 3)"))
            elif cmd == "x":
                try:
                    self.look(looks[int(arg) - 1])
                except (ValueError, IndexError):
                    print(dim("  look at what?"))
            elif raw.isdigit() or raw == "":
                n = int(raw) if raw.isdigit() else 1
                if not choices and n == 1:
                    self.beat += 1
                    self.save()
                    print()
                    return True
                if 1 <= n <= len(choices):
                    c = choices[n - 1]
                    print()
                    print(wrap("\u279c " + c.get("label", ""), "  "))
                    print()
                    for para in c.get("text", []):
                        print(wrap(para, "  "))
                        print()
                    self.beat += 1
                    self.save()
                    return True
                print(dim("  not one of the choices."))
            else:
                print(dim("  ? for help."))

    def endcard(self) -> bool:
        end = self.chapter.get("end") or {}
        print(dim("  ── ── ──"))
        print(bold("  " + end.get("title", "End")))
        print()
        for para in end.get("text", []):
            print(wrap(para, "  "))
            print()
        last = self.idx >= len(self.chapters) - 1
        if not end.get("nextLabel") or last:
            print(dim(wrap("This is where the played record stops. "
                           "The rest is unruled page.", "  ")))
            print()
            try:
                input(dim("  [enter] "))
            except (EOFError, KeyboardInterrupt):
                print()
            self.save()
            return False
        try:
            raw = input(dim("  [enter] " + end["nextLabel"] + " ")).strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            self.save()
            return False
        if raw in ("q", "quit", "exit"):
            self.save()
            print(dim("  saved.\n"))
            return False
        self.go(self.idx + 1)
        return True


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--repo", default=".", help="repository root (default: .)")
    ap.add_argument("--drafts", action="store_true",
                    help="include unratified drafts, marked as such")
    ap.add_argument("--pace", type=int, default=1,
                    help="passages revealed per keypress (default: 1)")
    ap.add_argument("--list", action="store_true", help="list fragments and exit")
    ap.add_argument("--quest", action="store_true",
                    help="play the hand-authored chapters from quest/index.html")
    args = ap.parse_args()
    root = os.path.abspath(args.repo)
    if args.quest:
        path = questfile.find_quest(root)
        if not path:
            print("No quest file found (looked for quest/index.html).")
            return 1
        data = questfile.load_quest(path)
        if args.list:
            for i, c in enumerate(data["chapters"], 1):
                print(f"{i:2d}  {c.get('title', '')}")
            return 0
        QuestPlayer(root, data).run()
        return 0
    t = Teller(root, args.drafts, args.pace)
    if args.list:
        for f in t.fragments:
            print(f.label)
        return 0
    t.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
