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

## What it does not do

**It invents nothing.** There is no model here and no generation: every
word it shows you is a word the author wrote. Authored branching is real
and this plays it; what it cannot do is make a choice nobody wrote.

## Scope and licence

The tool is engine, not world: MIT, like the rest of the engine. It holds
no story content of its own — point it at any repository with either shape
and that repository's words are what you get.
