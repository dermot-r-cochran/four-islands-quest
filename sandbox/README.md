# sandbox — the Sounds, ticking

A mini ecosystem of the Kingdom of the Four Sounds, one tide at a time.
Not a chapter and not a player: a small living model of the waters the
kingdom is named for, and of the two companies that work them every tide.

```bash
python3 sandbox/ecosystem.py                       # one tide-cycle, seed 1
python3 sandbox/ecosystem.py --tides 84 --seed 7   # three cycles, another world
python3 sandbox/ecosystem.py --quiet               # the summary only
python3 sandbox/ecosystem.py --ledger              # the Warden's ledger after the run
python3 sandbox/ecosystem.py --json                # the final state, for tools
python3 sandbox/ecosystem.py --check               # the invariants hold
```

## What it needs

Nothing. Python 3 standard library only — no dependencies, no network, no
model, nothing installed. It reads the companies it names out of
`index.html` through `teller/questfile.py`, the same non-executing parser
the terminal player uses, so it stands behind the same record as the
quest rather than keeping a second copy of it.

## What is in the water

- **The tide** — a 28-tide cycle, two tides a day, springs a fortnight
  apart. Everything else keys off it: the bloom, the shellfish's feeding
  time, when gulls fledge and seals pup, and how many times the bell
  rings.
- **The weather** — calm, fresh, blowing, or a storm, drawn each tide.
  It decides how well anything can work the water: a storm keeps the
  gulls ashore and the boats in, and scours the shores.
- **The bloom** in the Sounds, stirred up by the big tides and by storms.
- **Herring**, feeding on the bloom and fed on by everything else. When
  the Sounds run thin, a new shoal comes in on a spring tide — herring
  are travellers, and the kingdom is on their road.
- **Shellfish** on the three written shores. Gulls take them, more so
  when the water cannot be worked; First Island gathers them in fair
  weather, never more than a tenth of the shore.
- **Gulls** on every written shore, fishing when they can and fledging
  on the springs when they are fed. An empty shore is resettled from the
  largest colony on a calm tide.
- **Seals** on the skerries between Second and Third, fishing the same
  herring.
- **The ferry**, which crosses on any tide and is owed for it. Fares are
  paid in coin or in news; an empty crossing is logged as owed. What the
  passengers leave behind feeds the quay's gulls.
- **The Warden**, who writes down, every tide, what the Guild will not
  say aloud.

The sandbox settles to its own level after a few cycles — fewer gulls
than it started with, herring that thin and come back — which is what a
small water does. Nothing in it is tuned to be pretty.

## Two ledgers

The chronicle is the ferryman's voice: one line a tide, what happened
and whether it was worth a fare. It never counts the bell. The Warden's
ledger — `--ledger` — is the Crown's: tide, rings, how many aboard, how
much landed. The spine says the bell is not counted *aloud*; the record
of Chapter One says the Crown counts what the Guild won't. The sandbox
keeps both, and `--check` fails if the chronicle ever says the count.

## Between visits

```bash
python3 sandbox/ecosystem.py --state .ecosystem-state.json             # run, save
python3 sandbox/ecosystem.py --state .ecosystem-state.json             # continue
python3 sandbox/ecosystem.py --state .ecosystem-state.json --history   # the written past
```

With `--state`, the world keeps going where it left off — the nearest
thing a single file can do to presences that act between visits. The
state file is gitignored. Without `--state`, every run is a fresh world
from its seed, so two people running the same seed see the same Sounds.

## The past stays written

The randomness is one stream per tide, keyed on the seed and the tide
number. So a run continued from a save is the same run as one played
straight through, and reading a saved chronicle back never changes a
line of it. That is the spine's time-travel fact in the smallest form
the sandbox can carry, and `--check` proves it.

## Fourth Island

Listed, and not simulated. `WORLD.md` says there is nothing behind it
until it is written, and the sandbox holds it to that: no populations,
no events, a summary line that says *not simulated — nothing is written
of it*. Gulls that go south leave the record; the ones that come back do
not say where they were. `--check` fails if a run ever puts anything on
Fourth Island or names it in a chronicle line.

## Data and engine

The file has the same shape as `index.html`: a **WORLD DATA** section on
top — places, species, the weather, and every line the chronicle can say
— and an **engine** below it that adds no words of its own. Re-voice or
re-stock the sandbox by editing the data; the engine should not need
touching for that. The data is soft world content in `WORLD.md`'s sense:
on `main`, so part of the record, but no chapter owes it anything and a
later chapter may contradict it. It may not contradict the spine, and the
two spine facts it touches are pinned by `--check`.

## Licence

Split by section, like `index.html`: the WORLD DATA section is CC BY 4.0
and the engine is MIT — see `CONTENT-LICENSE.md`. This is this world's
own, not a shared tool: it is world-specific by design and is not kept
byte-identical with anything.
