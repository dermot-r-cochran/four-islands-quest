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
- Don't propose porting this onto a framework, engine, or server, and don't
  propose an authoring or builder mode. The single-file shape is the point.
  The reason is worth knowing, because it is why the heavier prototypes this
  descends from were left behind: **when you author *through* a builder, the
  artifact stops being your content and becomes the system's state** — not
  diffable, not readable end to end, not reviewable as a story. And builders
  are excellent at structure and useless at voice. A world that is mostly
  structure earns one; this is a world of trivial structure and nothing but
  voice, so the builder would have almost nothing to do while the document
  still had everything.
- **Evennia is permitted where it helps, and only where it is not heavyweight
  or overkill** (Dermot's direction, 2026-09-06 — which narrows the bullet
  above rather than repealing it). The line it draws: `index.html` and the
  tools stay dependency-free, framework-free and server-free; CI still
  installs nothing; the one-file engine remains the canonical player and the
  only authoring surface, so the builder reasoning above stands whole. An
  Evennia runner may stand *beside* them the way `teller/` does — a separate
  player of the same world data, in its own directory, optional to install,
  reading `index.html` rather than replacing it — for what a single file
  cannot do: several players in one world at once, a world that persists on
  a server, presences that act between visits. The test is the direction's
  own words. If the one-file engine or `teller` can already do the thing,
  Evennia is overkill for it; if the thing needs Evennia's whole stack
  present for one reader to open one chapter, it is too heavyweight. Nothing
  has been built on this yet, and the first thing that is should be able to
  say which of those two tests it passed.

## Commands

```bash
python3 tools/validate.py            # the world data holds together
python3 -m compileall -q teller tools # everything parses
python3 teller/teller.py --quest     # play it in a terminal
python3 teller/teller.py --quest --list
python3 sandbox/ecosystem.py         # the Sounds, one tide-cycle
python3 sandbox/ecosystem.py --check # the sandbox's invariants hold
```

Run `tools/validate.py` before committing — CI runs it too, along with the
parse gate, the sandbox's `--check`, a full scripted playthrough, a guard
that the shared tool stays world-agnostic, and a check that no build
artifacts are tracked. CI installs nothing, and should stay that way.

`.github/workflows/pages.yml` publishes `index.html` to GitHub Pages on
every push to `main` (https://dermot-r-cochran.github.io/four-islands-quest/).
It stages that one file and nothing else — the site is the quest; the
tools, the sandbox and the docs stay in the repository — and it installs
nothing either. Saves on the site live in that origin's localStorage, under
the same `four-islands-` keys as anywhere else.

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
repo is the record, six spine facts bind, everything else is soft, no hidden
canon exists, and the register stays general-audience. Read it before writing
world content, and keep it accurate if the spine changes.

**Time travel is in the spine** (Dermot's direction, 2026-09-06): it exists,
and it never alters an established past event. To the engine that costs
nothing — a chapter set in the past is an ordinary chapter with its own
`saveId`, its choices still converge, and nothing branches, which is exactly
why a past that cannot be altered fits this engine and a past that could
would not. To the content it binds: a past-set chapter may add what the
record never wrote and may not contradict a spine fact or a chapter that
stands on `main`. `tools/validate.py` cannot check it; it is a judgement the
author makes before committing.

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

## The sandbox

`sandbox/ecosystem.py` is a mini ecosystem of the Four Sounds (Dermot's
direction, 2026-09-06: *ecosystem mini sandbox*) — a third thing beside the
engine and `teller/`, standing beside them the way the Evennia bullet says a
second player may: its own directory, optional, reading `index.html` (the
companies it names come from `FACTIONS` through `questfile`) rather than
replacing it. One file, standard library only, the same shape as
`index.html`: a WORLD DATA section on top — places, species, the weather,
and every line the chronicle can say — and an engine below it that adds no
words. Re-voice or re-stock the sandbox by editing the data; the engine
should not need touching for that.

What it does: ticks one tide at a time on a 28-tide spring-and-neap cycle,
grows a bloom, herring, shellfish, gulls and seals against each other on
the water and browse, fallow deer and wolves against each other on the
hills (wolves on Second and Third, which have narrows between them; First
Island's deer answer to the Keep's huntsmen instead — Dermot's direction,
2026-09-06: *add wolves and fallow deer*), and every tide has the ferry
cross (on any tide, and owed for it — an empty
crossing is logged as owed) and the Warden write a ledger line the
chronicle never speaks: the bell's rings. `--state PATH` keeps a world
going between visits; `--history` shows its chronicle; `--ledger` shows
the Warden's. `--check` is its test and runs in CI.

Three rules it lives under, all consequences of `WORLD.md`:

- **Its data is soft world content.** It sits on `main`, so it is part of
  the record, but nothing in it is spine: no chapter owes the sandbox its
  numbers or its species, and a later chapter may contradict it freely.
  It is bounded the other way — nothing in it may contradict a spine fact,
  and `--check` pins the two it could: the ferry crosses every tide, and
  the bell is never counted aloud in the chronicle.
- **Fourth Island is listed and not simulated.** No hidden canon: there is
  nothing behind it until it is written, so the sandbox holds no
  populations there, prints *not simulated — nothing is written of it*,
  and `--check` fails if a run ever puts anything on it or names it in a
  chronicle line. Gulls that go south leave the record, and come back
  without saying where they were.
- **The written past stays written.** One random stream per tide, keyed
  on seed and tide number, so a run continued from a save is the run
  played straight through, and revisiting a saved chronicle never changes
  a line of it. `--check` proves both. This is the spine's time-travel
  fact in the smallest form the sandbox can carry.

Which of the Evennia tests it passed: neither, because it is not the
Evennia runner and does not use Evennia. It is *mini* on purpose — one
reader, one file, nothing that needs several players at once or a server
— so Evennia would have been too heavyweight for it by the direction's own
test, and the bullet above still says nothing has been built on Evennia
yet. If a runner is ever built, this is the kind of thing it would drive
between visits; until then the sandbox proves the model without the stack.

`sandbox/` is this world's own, not a shared tool: it is world-specific by
design, is not kept byte-identical with anything, and is not covered by the
world-agnostic guard.

## Before committing

Run `python3 tools/validate.py` (and `python3 sandbox/ecosystem.py --check`
if you touched the sandbox). It fails on what is always wrong — a beat
looking at an examinable that does not exist, two chapters sharing a
`saveId`, a company referencing an absent company, an endcard offering a
chapter that follows nothing — and warns on judgement calls, like an
examinable nothing looks at. Warnings are for a human to weigh, not to
silence.
