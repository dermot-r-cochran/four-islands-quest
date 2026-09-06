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

And on the hills above the shores:

- **Browse** on every written island, grazed by the deer. A stripped
  hill regrows from the root, slowly, and the chronicle says when a
  hill is stripped and when it greens again.
- **Fallow deer** on every written island, fawning when the hill feeds
  them and going hungry when it does not. Nothing grazes below the
  roots, so a stripped hill regrows from them, slowly. First Island's
  deer are the Keep's to hunt, in fair weather — the Keep's huntsmen are
  that island's wolves — and now and then one goes to the Keep's table.
- **Wolves**, in packs, on Second and Third, which have narrows between
  them. A pack is judged on its hunting rather than on one night's luck:
  it grows while the deer are many and goes short when they are few,
  and hunting falls away fast as a herd thins, which is what lets the
  herd come back. A pack that dies out is replaced from across the
  narrows at a calm neap, when the water between is narrowest. No wolves
  on First Island, whose deer answer to the Keep instead.
- **Rabbits** on every written island, grazing the same hill as the deer
  and breeding the way rabbits do. The chronicle says when they are
  everywhere and when they have thinned.
- **Squirrels** in the wood on every written island, living off the wood
  itself. A storm shakes the nuts down and they do well after it.
- **Foxes** on every written island: rabbits first, squirrels when they
  can get them, and the quay's scraps on First Island. They are judged
  on their hunting like the wolves, and cross the narrows the same way.
- **Cats** at the Keep and the quay on First Island, kept rather than
  wild. The kitchens keep a floor under them, so they never starve out;
  above it they live or die by the hunting like anything else, and now
  and then there are kittens at the Keep.

A few deer, a few rabbits and a fox or two always survive on a hill,
however bad it gets: hills have corners. Wolves do not get that; a pack
that runs out of deer runs out, and comes back only across the narrows.

The sandbox settles to its own level after a few cycles — fewer gulls
than it started with, herring that thin and come back, wolves and deer
chasing each other up and down — which is what a small water and three
small hills do. A pack can die out and a herd can crash; nothing in it
is tuned to be pretty.

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

Listed, and not simulated. `WORLD.md` holds one line of it — a few
hermits, and nothing more — and the sandbox holds it to exactly that: no
populations, no events, a summary line that says *not simulated — a few
hermits, and nothing else is written of it*. Gulls that go south leave the record; the ones that come back do
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
