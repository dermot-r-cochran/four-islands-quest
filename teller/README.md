# teller — a terminal player for this quest

Plays the Kingdom of the Four Sounds in a terminal, with the author's own
choices, examinables and companies — the same world `index.html` runs in a
browser, read straight out of the file.

```bash
python3 teller/teller.py --quest          # play
python3 teller/teller.py --quest --list   # list the chapters
python3 teller/teller.py --repo ../other  # point it at another repo
```

## What it needs

Nothing. Python 3 standard library only — no dependencies, no network, no
model, no configuration, and no JavaScript runtime.

`questfile.py` reads the world out of `index.html` by parsing the
JavaScript object literals it is stored in — `CHAPTERS`, `EXAMINE`,
`FACTIONS`, `CHAPTER_FACTIONS` — with a small recursive-descent reader.
**Nothing is executed.** It is a parser, not an interpreter, and it never
runs a line of the file it reads.

## Playing

```
  N         take that choice              x N      look at the Nth thing
  j         the quest log                 f        the companies present
  l         list chapters                 g N      go to chapter N
  r         restart this chapter          q        save and leave
  + TEXT    note a line for the author's review (+ alone: several lines)
```

Finishing a chapter shows its endcard and offers the way on, exactly as
the browser engine does. Progress saves to `.teller-progress.json` in the
repo root (gitignored) and resumes where you stopped.

## Reading mode

Run without `--quest` and it looks instead for a fragment-structured
story — `scenes/fragment-NNN.md` files, plus an optional `private-canon.md`
whose `## Log` becomes a record you can query with `a WORD` while reading.
This repository has no such directory; the mode is there because the tool
is written against the shape, not against this world.

## Pictures

The tool can offer pictures beside a story — but only ones the record
itself names, in a fragment's header, in a log entry it cites, or in an
optional `reference/fragments.json` sidecar. Nothing is matched by
guesswork.

`x` says what the record names for this fragment and how many pictures
the `reference/` tree holds, by folder; `x FOLDER` lists one folder, and
`v FOLDER/NAME` shows any picture there, named by the record or not; a
bare `v` shows the next picture here you have not yet seen. The
prompt itself carries the step's options after the dash; `--bare` gives a
plain dash instead.

This repository ships no pictures, so none are ever shown here. The
capability travels with the shared code because the tool is written
against the shape, not against any one world. `--images off` disables it
outright; images are never decoded or interpreted, only handed to the
terminal or the system viewer.

## Notes for review

`+ TEXT` at any prompt, in either mode, appends the line to `teller-inbox.md`
in the repo root, stamped with the time and the place in the story; `+` alone
takes several lines, ended by an empty one. The teller only ever appends to
that file and never reads it back, so nothing typed there reaches the story,
the record or the quest until a person moves it. It is the safe way to leave
fresh text, a scene idea or a choice for the author while reading.

## What it does not do

**It invents nothing.** There is no model here and no generation: every
word it shows you is a word the author wrote. Authored branching is real
and this plays it; what it cannot do is make a choice nobody wrote.

## A shared tool

`teller.py`, `questfile.py` and `images.py` are kept **byte-identical**
with the copy in the author's other story repository, on the same
discipline as any shared script: change one, land the same change in the
other in the same piece of work. Nothing world-specific lives in them.

## Scope and licence

The tool is engine, not world: MIT, like the rest of the engine. It holds
no story content of its own — point it at any repository with either shape
and that repository's words are what you get.
