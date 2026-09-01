"""questfile — read the hand-authored chapters out of a one-file quest engine.

The quest engine keeps its entire world in JavaScript object literals inside
`index.html`. This reads them **without executing anything**: a small
recursive-descent parser over the literal syntax actually used there —
objects, arrays, strings (including `+` concatenation across lines), numbers,
booleans, null, identifiers as keys, line and block comments, trailing commas.

Standard library only. Nothing here evaluates JavaScript.
"""

from __future__ import annotations

import os
import re

_ESCAPES = {"n": "\n", "t": "\t", "r": "\r", "\\": "\\", "/": "/",
            '"': '"', "'": "'", "`": "`", "b": "\b", "f": "\f", "0": "\0"}


class ParseError(ValueError):
    pass


class _Reader:
    def __init__(self, text: str, i: int = 0) -> None:
        self.s = text
        self.i = i

    def _ws(self) -> None:
        s = self.s
        while self.i < len(s):
            c = s[self.i]
            if c in " \t\r\n":
                self.i += 1
            elif s.startswith("//", self.i):
                j = s.find("\n", self.i)
                self.i = len(s) if j < 0 else j + 1
            elif s.startswith("/*", self.i):
                j = s.find("*/", self.i)
                self.i = len(s) if j < 0 else j + 2
            else:
                return

    def _at(self) -> str:
        if self.i >= len(self.s):
            raise ParseError("unexpected end of literal")
        return self.s[self.i]

    def _expect(self, ch: str) -> None:
        self._ws()
        if self._at() != ch:
            raise ParseError(f"expected {ch!r} at offset {self.i}")
        self.i += 1

    # -- values -------------------------------------------------------
    def value(self):
        self._ws()
        c = self._at()
        if c in "\"'`":
            return self.joined_string()
        if c == "[":
            return self.array()
        if c == "{":
            return self.obj()
        return self.word()

    def one_string(self) -> str:
        quote = self._at()
        self.i += 1
        out = []
        while True:
            c = self._at()
            self.i += 1
            if c == quote:
                return "".join(out)
            if c != "\\":
                out.append(c)
                continue
            e = self._at()
            self.i += 1
            if e == "u":
                out.append(chr(int(self.s[self.i:self.i + 4], 16)))
                self.i += 4
            elif e == "\n":
                pass  # line continuation
            else:
                out.append(_ESCAPES.get(e, e))

    def joined_string(self) -> str:
        parts = [self.one_string()]
        while True:
            save = self.i
            self._ws()
            if self.i < len(self.s) and self.s[self.i] == "+":
                self.i += 1
                self._ws()
                if self.i < len(self.s) and self._at() in "\"'`":
                    parts.append(self.one_string())
                    continue
            self.i = save
            return "".join(parts)

    def array(self) -> list:
        self._expect("[")
        out = []
        while True:
            self._ws()
            if self._at() == "]":
                self.i += 1
                return out
            out.append(self.value())
            self._ws()
            if self._at() == ",":
                self.i += 1

    def obj(self) -> dict:
        self._expect("{")
        out = {}
        while True:
            self._ws()
            if self._at() == "}":
                self.i += 1
                return out
            key = self.one_string() if self._at() in "\"'" else self.bare_key()
            self._expect(":")
            out[key] = self.value()
            self._ws()
            if self._at() == ",":
                self.i += 1

    def bare_key(self) -> str:
        m = re.compile(r"[A-Za-z_$][A-Za-z0-9_$]*").match(self.s, self.i)
        if not m:
            raise ParseError(f"bad key at offset {self.i}")
        self.i = m.end()
        return m.group(0)

    def word(self):
        m = re.compile(r"-?[A-Za-z0-9_.+$]+").match(self.s, self.i)
        if not m:
            raise ParseError(f"bad value at offset {self.i}")
        self.i = m.end()
        raw = m.group(0)
        if raw == "true":
            return True
        if raw == "false":
            return False
        if raw in ("null", "undefined"):
            return None
        try:
            return int(raw)
        except ValueError:
            pass
        try:
            return float(raw)
        except ValueError:
            return raw


def parse_const(text: str, name: str):
    """Return the literal assigned to `const NAME = ...`, or None."""
    m = re.search(r"\bconst\s+" + re.escape(name) + r"\s*=\s*", text)
    if not m:
        return None
    try:
        return _Reader(text, m.end()).value()
    except ParseError:
        return None


def find_quest(root: str) -> str | None:
    for rel in ("quest/index.html", "index.html"):
        path = os.path.join(root, rel)
        if os.path.isfile(path):
            return path
    return None


def load_quest(path: str) -> dict:
    """Read a quest engine file into plain Python data."""
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    chapters = parse_const(text, "CHAPTERS") or []
    return {
        "path": path,
        "chapters": chapters,
        "examine": parse_const(text, "EXAMINE") or {},
        "factions": parse_const(text, "FACTIONS") or {},
        "chapter_factions": parse_const(text, "CHAPTER_FACTIONS") or {},
    }
