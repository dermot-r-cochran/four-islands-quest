"""images — find and show the pictures a record names.

Nothing here decodes or interprets image data, and nothing is invented: an
image is offered for a fragment only when the record itself names it — in the
fragment's own header, in a log entry that fragment cites, or in an optional
author-written sidecar.

Display is layered, and every layer is standard library:

  inline   terminals that speak a graphics protocol get the bytes base64'd
           (iTerm2/WezTerm: any format; kitty: PNG only, since anything else
           would need decoding and decoding would need a dependency)
  open     otherwise the file is handed to the system viewer
  name     otherwise its path is printed, which is still an answer

A repository with no pictures simply never shows any; the capability is
written against the shape, like the rest of the tool.
"""

from __future__ import annotations

import base64
import json
import os
import re
import subprocess
import sys

IMAGE_EXT = (".jpg", ".jpeg", ".png", ".gif", ".webp")
MEDIA_DIRS = ("reference", "images", "media")
SIDECAR = "fragments.json"

# `dir/name.ext`, `name.ext`, or a backticked bare stem — backticks required
# for stems so ordinary prose can never be mistaken for a filename.
PATH_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_/-]*\.(?:jpe?g|png|gif|webp)")
STEM_RE = re.compile(r"`([A-Za-z0-9][A-Za-z0-9_-]{2,})`")


def index_media(root: str) -> dict[str, str]:
    """Map every image under the media directories by path tail and by stem."""
    out: dict[str, str] = {}
    for d in MEDIA_DIRS:
        base = os.path.join(root, d)
        if not os.path.isdir(base):
            continue
        for dirpath, _dirs, files in os.walk(base):
            for name in files:
                if not name.lower().endswith(IMAGE_EXT):
                    continue
                full = os.path.join(dirpath, name)
                rel = os.path.relpath(full, root).replace(os.sep, "/")
                out.setdefault(rel, full)
                out.setdefault(rel.split("/", 1)[-1], full)
                out.setdefault(name, full)
                out.setdefault(os.path.splitext(name)[0], full)
    return out


def named_in(text: str, index: dict[str, str]) -> list[str]:
    """Every indexed image the given text actually names, in order."""
    found: list[str] = []
    for m in PATH_RE.finditer(text):
        hit = index.get(m.group(0)) or index.get(m.group(0).split("/")[-1])
        if hit and hit not in found:
            found.append(hit)
    for m in STEM_RE.finditer(text):
        hit = index.get(m.group(1))
        if hit and hit not in found:
            found.append(hit)
    return found


def sidecar(root: str) -> dict[str, list[str]]:
    """Optional author-written map: {"017": ["places/castle-balcony.png"]}."""
    for d in MEDIA_DIRS:
        path = os.path.join(root, d, SIDECAR)
        if os.path.isfile(path):
            try:
                with open(path, encoding="utf-8") as fh:
                    data = json.load(fh)
                return {str(k): list(v) for k, v in data.items()}
            except Exception:
                return {}
    return {}


# -- display ----------------------------------------------------------
def protocol() -> str | None:
    if not sys.stdout.isatty():
        return None
    if os.environ.get("TERM_PROGRAM") in ("iTerm.app", "WezTerm"):
        return "iterm"
    if os.environ.get("KITTY_WINDOW_ID") or "kitty" in os.environ.get("TERM", ""):
        return "kitty"
    return None


def _inline(path: str, proto: str) -> bool:
    try:
        with open(path, "rb") as fh:
            raw = fh.read()
    except OSError:
        return False
    b64 = base64.b64encode(raw).decode("ascii")
    if proto == "iterm":
        name = base64.b64encode(os.path.basename(path).encode()).decode("ascii")
        sys.stdout.write(
            f"\033]1337;File=name={name};size={len(raw)};inline=1;"
            f"height=20:{b64}\a\n"
        )
        return True
    if proto == "kitty" and path.lower().endswith(".png"):
        for i in range(0, len(b64), 4096):
            chunk = b64[i:i + 4096]
            more = 1 if i + 4096 < len(b64) else 0
            head = "a=T,f=100," if i == 0 else ""
            sys.stdout.write(f"\033_G{head}m={more};{chunk}\033\\")
        sys.stdout.write("\n")
        return True
    return False


def _launch(path: str) -> bool:
    try:
        if sys.platform == "darwin":
            subprocess.Popen(["open", path], stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL)
        elif sys.platform.startswith("win"):
            os.startfile(path)  # type: ignore[attr-defined]
        else:
            subprocess.Popen(["xdg-open", path], stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL)
        return True
    except Exception:
        return False


def show(path: str, mode: str = "auto") -> str:
    """Show an image as well as this terminal allows. Returns a status line."""
    label = os.path.relpath(path)
    if mode == "off":
        return f"images are off — {label}"
    if mode in ("auto", "inline"):
        proto = protocol()
        if proto and _inline(path, proto):
            return label
        if mode == "inline":
            return f"this terminal has no inline graphics — {label}"
    if mode in ("auto", "open"):
        if _launch(path):
            return f"opened in your viewer — {label}"
    return label
