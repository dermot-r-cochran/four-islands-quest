# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with
code in this repository.

## What this is

A one-file browser quest engine with a small demo world aboard — the Kingdom
of the Four Sounds — plus a terminal player for the same world. Open
`index.html` in any browser: no server, no build, no dependencies, no
network, no framework. Progress saves to localStorage.

It is meant to be forked. The demo ends where somebody else's world begins,
and the repository is arranged so that the fastest path to a new world is
replacing data rather than writing code.

## The prime directive

**Everything the player can meet lives in four data structures at the top of
`index.html`, and the engine below them never needs editing to add content.**
Preserve that. It is the whole design, and most of the rules below are just
consequences of it:

- **No dependencies, no build step, no network calls, no framework.** Not in
  the page, not in the tools. If a change would add any of these, it is the
  wrong change — say so rather than making it.
- **One reviewable file.** The world diffs cleanly in git because it is plain
  literals in one place. Don't split it, minify it, or move content into JSON
  the page fetches (that would need a server).
- **Never rewrite `index.html` programmatically.** Read it by all means —
  `teller/questfile.py` parses its literals without executing them — but
  round-tripping the file would lose formatting and comments and would put a
  program in a file a human edits. Author by hand or with an assistant.
- Don't propose porting this onto a framework, engine, or server. The
  single-file shape is the point; the engine descends from heavier prototypes
  that were deliberately left behind.

## Commands

```bash
python3 tools/validate.py            # the world data holds together
python3 -m compileall -q teller tools # everything parses
python3 teller/teller.py --quest     # play it in a terminal
python3 teller/teller.py --quest --list
```

Run `tools/validate.py` before committing — CI runs it too, along with the
parse gate, a full scripted playthrough, a guard that the shared tool stays
world-agnostic, and a check that no build artifacts are tracked. CI installs
nothing, and should stay that way.

## The world data

`index.html`, between the `WORLD DATA` and `ENGINE` banners.

- **`CHAPTERS`** — an array of
  `{saveId, title, sub, end, heldLine, beats}`.
  - `end` is `{title, text: [paragraphs], nextLabel}`. Set `nextLabel` only
    when a next chapter exists; the last chapter's is `null`.
  - `heldLine` names what has not been reached yet — it shows at the foot of
    the quest log, and on the last chapter it names what is not yet written.
- **A beat** is `{id, log, presences, examine, enter, choices}`.
  - `log` is the quest-log stage; `presences` is the who-and-what-is-here
    list; `examine` is an array of `EXAMINE` keys; `enter` is the beat's prose
    as plain-text paragraphs.
  - `choices` is `[{label, text}]`, and **every choice converges on the same
    next beat**. Choices are texture, not branching: different ways to arrive
    where the story arrives. A beat with no choices takes an optional
    `continueLabel`.
- **`EXAMINE`** — `{key: {label, text}}`, shared across chapters.
- **`FACTIONS`** — `{key: {name, seat, quest, members, of, sub}}`. Companies
  nest via `of` (parent key) and `sub` (child keys).
- **`CHAPTER_FACTIONS`** — `{saveId: [faction keys]}`, choosing which
  companies stand behind each chapter.

### saveId is an identity, not a number

`saveId` keys a chapter's saved progress. It must be **stable and unique**,
and it is deliberately not the chapter's position: that is what makes
inserting a chapter mid-sequence safe, because nobody's save is orphaned.
Never renumber, reuse, or "tidy" a `saveId` — changing one silently discards
the progress of everyone who has played that chapter. Adding one is free.

### Adding a chapter

Append to `CHAPTERS` (and any new examinables to `EXAMINE`), give the
previous chapter's `end.nextLabel` a value so it flows on, add a
`CHAPTER_FACTIONS` row if companies stand behind it, then run
`tools/validate.py`. Strings are written as `"…" + "…"` concatenation across
lines to keep the file readable — follow that.

## Governance

**`WORLD.md` is the entire canon apparatus** and is deliberately minimal: the
repo is the record, five spine facts bind, everything else is soft, no hidden
canon exists, and the register stays general-audience. Read it before writing
world content, and keep it accurate if the spine changes.

The demo world is the author's pen. **Code contributions are welcome; story
changes belong in a fork** — see `CONTENT-LICENSE.md`.

## Licensing is split by section

- **Engine — MIT** (`LICENSE`): everything outside the `WORLD DATA` section,
  plus `teller/` and `tools/`.
- **Demo world content — CC BY 4.0** (`CONTENT-LICENSE.md`): the prose and
  data inside `WORLD DATA`.

Know which side a change falls on. A forker who replaces the world data owns
what they write, under the MIT engine terms alone.

## The shared tools

`teller/teller.py`, `teller/questfile.py`, `teller/images.py` and
`tools/validate.py` are kept **byte-identical with a copy in another
repository**. Two consequences:

- **Never put world-specific content into them.** They are written against
  the *shape* — fragment files, quest literals — not against this world. CI
  fails if they pick up this world's vocabulary.
- Change one and the same change must land in the sibling. If you are only
  working here, keep changes to these files minimal and general.

`teller` also has a reading mode for `scenes/fragment-NNN.md` stories, which
this repository does not have. That is not dead code; it is the other shape
the tool supports.

## Before committing

Run `python3 tools/validate.py`. It fails on what is always wrong — a beat
looking at an examinable that does not exist, two chapters sharing a
`saveId`, a company referencing an absent company, an endcard offering a
chapter that follows nothing — and warns on judgement calls, like an
examinable nothing looks at. Warnings are for a human to weigh, not to
silence.
