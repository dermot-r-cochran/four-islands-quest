#!/usr/bin/env python3
"""validate — structural checks for a quest engine and a fragment story.

Checks whatever the repository actually contains: the quest engine's world
data if there is a quest file, the fragments if there is a `scenes/`
directory, or both. Standard library only — nothing to install, in CI or out.

Failures are things that are always wrong (a beat pointing at an examinable
that does not exist, two chapters sharing a save id). Warnings are judgement
calls left to the author (an examinable nothing looks at).

    python3 tools/validate.py [--repo PATH] [--strict]

Exit status is non-zero if anything failed; `--strict` also fails on warnings.
"""

from __future__ import annotations

import argparse
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "teller"))
import questfile  # noqa: E402

TITLE_RE = re.compile(
    r"^#\s*Fragment\s+(\d+)\s*[—-]\s*(.+?)\s*\((APPROVED[^)]*|DRAFT)\)\s*$")

fails: list[str] = []
warns: list[str] = []


def fail(msg: str) -> None:
    fails.append(msg)


def warn(msg: str) -> None:
    warns.append(msg)


def check_quest(root: str) -> bool:
    path = questfile.find_quest(root)
    if not path:
        return False
    where = os.path.relpath(path, root)
    data = questfile.load_quest(path)
    chapters = data["chapters"]
    examine = data["examine"]
    factions = data["factions"]
    cfactions = data["chapter_factions"]

    if not chapters:
        fail(f"{where}: CHAPTERS did not parse, or is empty")
        return True
    for name, value in (("EXAMINE", examine), ("FACTIONS", factions),
                        ("CHAPTER_FACTIONS", cfactions)):
        if value and not isinstance(value, dict):
            fail(f"{where}: {name} is not an object")

    seen: dict[str, int] = {}
    used_examine: set[str] = set()
    for i, ch in enumerate(chapters):
        tag = f"{where}: chapter {i + 1}"
        save = ch.get("saveId")
        if not save:
            fail(f"{tag} has no saveId")
        elif save in seen:
            fail(f"{tag} reuses saveId {save!r} (also chapter {seen[save] + 1})"
                 " — saves would collide")
        else:
            seen[save] = i
        if not ch.get("title"):
            fail(f"{tag} has no title")
        if not ch.get("heldLine"):
            warn(f"{tag} has no heldLine")
        end = ch.get("end") or {}
        if not end.get("title") or not end.get("text"):
            fail(f"{tag} has no complete endcard")
        if end.get("nextLabel") and i == len(chapters) - 1:
            fail(f"{tag} is last but its endcard offers a next chapter")
        if not end.get("nextLabel") and i < len(chapters) - 1:
            warn(f"{tag} has no nextLabel, so play stops there")
        beats = ch.get("beats") or []
        if not beats:
            fail(f"{tag} has no beats")
        for j, b in enumerate(beats):
            btag = f"{tag} beat {j + 1}"
            for field in ("id", "log"):
                if not b.get(field):
                    fail(f"{btag} has no {field}")
            if not b.get("enter"):
                fail(f"{btag} has no enter text")
            for key in b.get("examine") or []:
                used_examine.add(key)
                if key not in examine:
                    fail(f"{btag} looks at {key!r}, which is not in EXAMINE")
            for k, c in enumerate(b.get("choices") or [], 1):
                if not c.get("label"):
                    fail(f"{btag} choice {k} has no label")
                if not c.get("text"):
                    fail(f"{btag} choice {k} has no text")

    for save, keys in (cfactions or {}).items():
        if save not in seen:
            fail(f"{where}: CHAPTER_FACTIONS names {save!r}, which is no chapter")
        for key in keys:
            if key not in factions:
                fail(f"{where}: CHAPTER_FACTIONS[{save!r}] names {key!r}, "
                     "which is not in FACTIONS")
    for key, f in (factions or {}).items():
        for ref in ([f.get("of")] if f.get("of") else []) + list(f.get("sub") or []):
            if ref not in factions:
                fail(f"{where}: FACTIONS[{key!r}] references {ref!r}, "
                     "which is not a company")
        if not f.get("name"):
            fail(f"{where}: FACTIONS[{key!r}] has no name")
    listed = {k for keys in (cfactions or {}).values() for k in keys}
    for key in factions or {}:
        if key not in listed:
            warn(f"{where}: company {key!r} stands behind no chapter")
    for key in examine or {}:
        if key not in used_examine:
            warn(f"{where}: examinable {key!r} is never looked at")

    # a scripted walk of every chapter, taking the first choice each time
    for ch in chapters:
        for b in ch.get("beats") or []:
            if not (b.get("choices") or b.get("continueLabel") is not None
                    or b.get("choices") == []):
                fail(f"{where}: {ch.get('saveId')} beat {b.get('id')} "
                     "offers no way onward")
    print(f"  quest: {len(chapters)} chapters, "
          f"{sum(len(c.get('beats') or []) for c in chapters)} beats, "
          f"{len(examine)} examinables, {len(factions)} companies")
    return True


def check_fragments(root: str) -> bool:
    scenes = os.path.join(root, "scenes")
    if not os.path.isdir(scenes):
        return False
    numbers: dict[int, str] = {}
    approved = drafts = 0
    names = [n for n in sorted(os.listdir(scenes))
             if n.startswith("fragment-") and n.endswith(".md")]
    for name in names:
        with open(os.path.join(scenes, name), encoding="utf-8") as fh:
            lines = fh.read().splitlines()
        if not lines:
            fail(f"scenes/{name} is empty")
            continue
        m = TITLE_RE.match(lines[0])
        if not m:
            fail(f"scenes/{name}: first line is not a "
                 "`# Fragment NNN — title (APPROVED …|DRAFT)` heading")
            continue
        num = int(m.group(1))
        stem = re.search(r"(\d+)", name)
        if stem and int(stem.group(1)) != num:
            fail(f"scenes/{name} is numbered {num} in its title")
        if num in numbers:
            fail(f"scenes/{name} reuses fragment number {num} "
                 f"(also {numbers[num]})")
        numbers[num] = name
        if m.group(3).startswith("APPROVED"):
            approved += 1
        else:
            drafts += 1
        body_at = next((i for i, ln in enumerate(lines) if ln.strip() == "---"),
                       None)
        if body_at is None:
            fail(f"scenes/{name} has no `---` rule between header and prose")
        elif not any(ln.strip() for ln in lines[body_at + 1:]):
            fail(f"scenes/{name} has no prose after the rule")
        header = "\n".join(lines[1:body_at]) if body_at else ""
        if m.group(3).startswith("APPROVED") and not re.search(r"Log\s+\d+",
                                                               header):
            warn(f"scenes/{name} is approved but cites no Log entry")
    print(f"  fragments: {len(names)} files, {approved} ratified, "
          f"{drafts} draft")
    return True


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--repo", default=os.path.join(
        os.path.dirname(os.path.abspath(__file__)), ".."))
    ap.add_argument("--strict", action="store_true",
                    help="treat warnings as failures")
    args = ap.parse_args()
    root = os.path.abspath(args.repo)
    print(f"validating {root}")
    found = [check_quest(root), check_fragments(root)]
    if not any(found):
        print("nothing to validate: no quest file and no scenes/ directory")
        return 1
    for w in warns:
        print(f"  warn: {w}")
    for f in fails:
        print(f"  FAIL: {f}")
    print(f"\n{len(fails)} failure(s), {len(warns)} warning(s)")
    return 1 if fails or (args.strict and warns) else 0


if __name__ == "__main__":
    raise SystemExit(main())
