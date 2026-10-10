#!/usr/bin/env python3
"""check_docs — the repository's Markdown holds together. Standard library only.

Three checks, all on the sources, none needing a build:

1. Every relative link in a Markdown file resolves to a file or directory
   in the repository. External links (any scheme) and in-page anchors are
   not checked.
2. No Markdown file carries more than one front-matter block — the shape a
   stray fragment left by a merge takes.
3. The counts the README states match what is on disk: the data structures
   in `index.html`, the sandbox's editions, the spine facts in `WORLD.md`,
   and the page-shell strings at the lines the README names.

This file is this repository's own; it is not one of the shared tools.

    python3 tools/check_docs.py [--repo PATH]

Exit status is non-zero if anything failed.
"""

from __future__ import annotations

import argparse
import os
import re
import sys

SKIP_DIRS = {".git", "__pycache__", "_site", "node_modules"}
LINK = re.compile(r"\]\(\s*<?([^)\s>]+)>?(?:\s+\"[^\"]*\")?\s*\)")
SCHEME = re.compile(r"^[a-z][a-z0-9+.-]*:", re.IGNORECASE)
INLINE_CODE = re.compile(r"`[^`\n]*`")
FRONT_KEY = re.compile(r"^[a-z_][a-z0-9_-]*\s*:")
WORDS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
         "seven": 7, "eight": 8, "nine": 9, "ten": 10}

fails: list[str] = []


def fail(msg: str) -> None:
    fails.append(msg)


def markdown_files(root: str) -> list[str]:
    found = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in filenames:
            if name.lower().endswith(".md"):
                found.append(os.path.join(dirpath, name))
    return sorted(found)


def read(path: str) -> str:
    with open(path, encoding="utf-8") as fh:
        return fh.read().replace("\r\n", "\n")


def prose_lines(text: str) -> list[tuple[int, str]]:
    """Lines outside fenced code blocks, with inline code removed."""
    kept, fenced = [], False
    for number, line in enumerate(text.split("\n"), start=1):
        if line.lstrip().startswith("```"):
            fenced = not fenced
            continue
        if not fenced:
            kept.append((number, INLINE_CODE.sub("", line)))
    return kept


def check_links(root: str, path: str, text: str) -> None:
    rel = os.path.relpath(path, root).replace(os.sep, "/")
    for number, line in prose_lines(text):
        for match in LINK.finditer(line):
            target = match.group(1)
            if SCHEME.match(target) or target.startswith("#"):
                continue
            plain = target.split("#", 1)[0].split("?", 1)[0]
            if not plain:
                continue
            if plain.startswith("/"):
                fail(f"{rel}:{number}: link {target!r} is root-absolute; "
                     "links here are relative to the file")
                continue
            resolved = os.path.normpath(os.path.join(os.path.dirname(path),
                                                     plain))
            if not os.path.exists(resolved):
                fail(f"{rel}:{number}: link {target!r} resolves to nothing")


def front_matter_blocks(text: str) -> int:
    """Count `---` blocks whose first line is a `key:` line — front matter,
    wherever it sits. A horizontal rule between paragraphs is not one."""
    lines = text.split("\n")
    count, i = 0, 0
    while i < len(lines):
        if lines[i].strip() == "---":
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            if j < len(lines) and FRONT_KEY.match(lines[j]):
                k = j + 1
                while k < len(lines) and lines[k].strip() != "---":
                    k += 1
                if k < len(lines):
                    count += 1
                    i = k + 1
                    continue
        i += 1
    return count


def check_front_matter(root: str, path: str, text: str) -> None:
    rel = os.path.relpath(path, root).replace(os.sep, "/")
    n = front_matter_blocks(text)
    if n > 1:
        fail(f"{rel}: {n} front-matter blocks; a file carries at most one")


def number(word: str) -> int:
    return WORDS.get(word.lower()) or int(word)


def stated(readme: str, pattern: str, what: str) -> int | None:
    """The number the README states in `pattern` (one group, a word or
    digits). Absent, the claim is gone and the check must be retired."""
    m = re.search(pattern, readme)
    if not m:
        fail(f"README.md no longer states {what}; retire or update the "
             "check in tools/check_docs.py")
        return None
    return number(m.group(1))


def compare(what: str, said: int | None, disk: int, where: str) -> None:
    if said is not None and said != disk:
        fail(f"README.md says {said} {what}; {where} has {disk}")


def data_structures(root: str) -> int:
    html = read(os.path.join(root, "index.html"))
    start, end = html.find("WORLD DATA"), html.find("ENGINE")
    section = html[start:end] if 0 <= start < end else ""
    return len(re.findall(r"^const [A-Z_]+ = ", section, re.M))


def editions(root: str) -> int:
    src = read(os.path.join(root, "sandbox", "ecosystem.py"))
    m = re.search(r"^EDITIONS = \{\n(.*?)^\}", src, re.M | re.S)
    if not m:
        return 0
    return len(re.findall(r'^    "[a-z]+": \{', m.group(1), re.M))


def spine_facts(root: str) -> int:
    world = read(os.path.join(root, "WORLD.md"))
    m = re.search(r"^## The spine.*?\n(.*?)(?=^## )", world, re.M | re.S)
    return len(re.findall(r"^- ", m.group(1), re.M)) if m else 0


def check_counts(root: str) -> None:
    readme_path = os.path.join(root, "README.md")
    if not os.path.isfile(readme_path):
        return
    readme = read(readme_path)

    compare("data structures",
            stated(readme, r"\b(\w+) data structures\b", "the data-structure count"),
            data_structures(root), "index.html's WORLD DATA section")
    compare("editions",
            stated(readme, r"\b(\w+) chronicles\b", "the edition count"),
            editions(root), "sandbox/ecosystem.py's EDITIONS")
    compare("files handed to Pages",
            stated(readme, r"hands all (\w+) to Pages", "what Pages is handed"),
            editions(root) + 1, "index.html plus the editions")
    compare("spine facts",
            stated(readme, r"\b(\w+) spine facts\b", "the spine-fact count"),
            spine_facts(root), "WORLD.md's spine")

    # the shell strings a fork replaces by hand, at the lines the README names
    html_lines = read(os.path.join(root, "index.html")).split("\n")
    shell = [
        (r"lines (\d+) and \d+ of\s+`index\.html`", "The Kingdom of the Four Sounds"),
        (r"lines \d+ and (\d+) of\s+`index\.html`", "The Kingdom of the Four Sounds"),
        (r"\"The Crossing\" \(line (\d+)\)", "The Crossing"),
        (r"daily page \(line\s+(\d+)\)", 'href="sounds/"'),
    ]
    for pattern, needle in shell:
        m = re.search(pattern, readme)
        if not m:
            fail(f"README.md no longer names the line of {needle!r}; retire or "
                 "update the check in tools/check_docs.py")
            continue
        n = int(m.group(1))
        line = html_lines[n - 1] if 0 < n <= len(html_lines) else ""
        if needle not in line:
            fail(f"README.md says index.html line {n} holds {needle!r}; "
                 f"it holds {line.strip()!r}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--repo", default=os.path.join(
        os.path.dirname(os.path.abspath(__file__)), ".."))
    args = ap.parse_args()
    root = os.path.abspath(args.repo)
    files = markdown_files(root)
    for path in files:
        text = read(path)
        check_links(root, path, text)
        check_front_matter(root, path, text)
    check_counts(root)
    for f in fails:
        print(f"  FAIL: {f}")
    print(f"docs: {len(files)} Markdown files, {len(fails)} failure(s)")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
