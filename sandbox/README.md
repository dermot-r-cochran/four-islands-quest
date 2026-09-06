# sandbox — the Sounds, ticking

A mini ecosystem of the Kingdom of the Four Sounds, one tide at a time.
Not a chapter and not a player: a small living model of the waters the
kingdom is named for, and of the two companies that work them every tide
— and, in its own edition, of Fourth Island, which nobody points at.

```bash
python3 sandbox/ecosystem.py                       # one tide-cycle, seed 1
python3 sandbox/ecosystem.py --tides 84 --seed 7   # three cycles, another world
python3 sandbox/ecosystem.py --quiet               # the summary only
python3 sandbox/ecosystem.py --ledger              # the Warden's ledger after the run
python3 sandbox/ecosystem.py --json                # the final state, for tools
python3 sandbox/ecosystem.py --html sounds.html    # the chronicle as a page
python3 sandbox/ecosystem.py --edition fourth      # Fourth Island's own account
python3 sandbox/ecosystem.py --edition sea         # the open sea, seen from a deck
python3 sandbox/ecosystem.py --check               # the invariants hold, both editions
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
- **Puffins** on the skerries beside them, fishing the same herring
  again and fledging on the springs when the fishing has been good.
- **The ferry**, which crosses on any tide and is owed for it. Fares are
  paid in coin or in news; an empty crossing is logged as owed. What the
  passengers leave behind feeds the quay's gulls.
- **The Warden**, who writes down, every tide, what the Guild will not
  say aloud.

And on the hills above the shores:

- **Grazing** on every written island (the sandbox's key for it is
  `browse`, the keeper's word; the page says *grazing*, since on a page
  *browse* reads as a verb). Eaten by the deer, the goats and the
  rabbits; nothing grazes below the roots, a stripped hill regrows from
  them slowly, and the chronicle says when a hill is stripped and when
  it greens again.
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
- **Small birds** in the hedges and the wood on every written island, on
  the worms in the turf all year — which come up in wet weather more than
  dry — and on the berries the wood sets in autumn and winter takes back.
  They are what the sparrowhawks and the Keep's cats hunt.
- **Foxes** on every written island: rabbits first, squirrels when they
  can get them, and the quay's scraps on First Island. They are judged
  on their hunting like the wolves, and cross the narrows the same way.
- **Cats** at the Keep and the quay on First Island, kept rather than
  wild. The kitchens keep a floor under them, so they never starve out;
  above it they live or die by the hunting like anything else, and now
  and then there are kittens at the Keep.
- **Wild goats** on every written island. They graze the hill with the
  deer, but the crags feed them what the hill does not — the sandbox
  does not count crag-browse, only that goats always find some — and
  the wolves take one now and then.
- **Hen harriers** over the moor on Second and Third, and
  **sparrowhawks** in the wood on every written island. Each lives on
  one prey the sandbox counts — rabbits for the harriers, squirrels for
  the hawks — and on the small birds and voles it does not, and fledges
  on the springs when fed.
- **Dragonflies** over the pools on every written island. A calm spell
  hatches them, a storm knocks them down, and the pools always hold a
  few more. The chronicle says when they are over every pool in the
  kingdom.
- **Ponies and alpacas**, the Keep's stock on First Island, kept like
  the cats: they graze the hill when it has grazing and eat the Keep's
  hay when it does not, so they never go short; now and then there is a
  foal in the stable or a cria among the alpacas.

A few deer, a few rabbits and a fox or two always survive on a hill,
however bad it gets: hills have corners. Wolves do not get that; a pack
that runs out of deer runs out, and comes back only across the narrows.

The sandbox settles to its own level after a few cycles — fewer gulls
than it started with, herring that thin and come back, wolves and deer
chasing each other up and down — which is what a small water and three
small hills do. A pack can die out and a herd can crash; nothing in it
is tuned to be pretty.

## The year

The sandbox keeps a year of 730 tides, two a day, and the springs and
neaps keep their own 28-tide count inside it — the tide words are
*springs*, *neaps* and *middling*, the sailors' plurals, so that a
season called spring is never mistaken for a tide. Winter opens the
year; spring comes in on the first of March, summer on the first of
June, autumn on the first of September, and the chronicle says so on
the tide each comes in. A season sets the odds of the weather (winter
blows and storms, summer is mostly calm), the level the bloom settles
toward, how fast the grazing, the shore and the wood grow, and how
hard hunger bites. Every species breeds in its own seasons — fawns and
kids in spring, gulls and puffins fledging through spring and summer,
seal pups in autumn, the wood's mast in autumn, dragonflies hatching
only in the warm half — and the puffins are at sea for the winter,
neither fed nor lost. `--date` starts a run on that day of the year, so
the page for a September morning is an autumn cycle.

## Who does what

Every species carries a role, and the page lists them under it: what
**grows** (the bloom, the grazing, the wood, the shellfish beds), what
**feeds** on it, what **hunts** and keeps the feeders in check, what
**picks up after** the hunters and the tide, and what **is kept** by
the Keep. The roles are not only labels: a deer or a goat the wolves
bring down is carrion on the next tide, and the gulls and the foxes
feed on it — *gulls on the wolves' kill* is the line — which is what
the scavengers are for.

## Two ledgers

The chronicle is the ferryman's voice: one line a tide, what happened
and whether it was worth a fare. It never counts the bell. The Warden's
ledger — `--ledger` — is the Crown's: tide, rings, how many aboard, how
much landed. The spine says the bell is not counted *aloud*; the record
of Chapter One says the Crown counts what the Guild won't. The sandbox
keeps both, and `--check` fails if the chronicle ever says the count.

## On the site

`--html PATH` writes the chronicle and the summary as one self-contained
page in the quest's palette, with the companies on the water at its head
and a link back to the quest. It leaves the Warden's ledger out, since
the bell is not counted aloud, and `--check` fails if a page ever shows
it. The Pages workflow runs this once a day with the date as the seed, so
every reader sees the same Sounds for the same day, at `/sounds/`, the
same Fourth Island at `/fourth/` and the same sea at `/sea/`; each page
points at the others.

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

## The open sea

The rest of the known world, in a third edition, `--edition sea`, as
seen from a deck: the plankton, the sea's own bloom; the shoals that
feed on it, too many to count; the dolphins that live on the shoals;
the whales that come in for the plankton in summer and autumn and go,
wherever they go, for the rest of the year; and south of Fourth Island,
in shallower water, the coral, which the warm seasons grow and the
storms break, with the reef fish that live on it. Nobody keeps an
account out here, so the voice is what a sailor might have told, had a
sailor come in, and a quiet tide has its own ways of being quiet —
*flat calm to the edge of the world*. `--check` fails if the account
ever mentions the ferry, a fare, the Guild, the Warden, a ledger or a
quay, and if the whales neither come nor go in a year.

## Fourth Island

Its own edition, `--edition fourth`, running the ground `WORLD.md` wrote
for it: one island south of the three, alone, the Sounds ending on its
northern shore and open sea beyond; a hill with a stony shore, cliffs, a
wood and pools; gulls on the cliffs, goats on the crags, rabbits and
harriers on the hill, squirrels and sparrowhawks in the wood,
dragonflies over the pools, shellfish on the shore and the Sounds'
herring off it. No narrows join it to anything, so nothing crosses on
foot: no deer, no wolves, no foxes, and nothing kept.

**The hermits are a presence, never a count.** They are sailors — some
came ashore by choice, some the sea put there, and the account never
says which — and now and then one more arrives on a calm tide or is
stranded by a storm; the account says so and counts nobody. They gather
on the shore in fair weather and take a goat now and then; their smoke
shows on a calm tide. There is no ferry, so no fare, no Guild and no Warden, and
nobody counts a tide aloud — the kingdom's one tide-calendar is borrowed
for the numbering. The account is what a hermit might have noticed, in
its own words for the same events, and a quiet tide there has several
ways of being quiet. `--check` fails if the account ever mentions the
ferry, a fare, the Guild, the Warden, a ledger or a quay, counts the
bell, or counts the hermits.

**In the Sounds edition it is listed and not simulated**, because
ferrymen do not point at it, and `--check` fails if that run ever puts
anything on it or names it in a chronicle line. Gulls that go south
leave the ferryman's record; on Fourth Island gulls come in off the sea;
neither account ties the two, though `WORLD.md` does.

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
