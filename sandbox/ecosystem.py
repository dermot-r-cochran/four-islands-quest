#!/usr/bin/env python3
"""ecosystem — a mini sandbox of the Four Sounds, one tide at a time.

Not a chapter and not a player. A small living model of the waters the
kingdom is named for: the bloom the tide stirs up, the herring that feed on
it, the shellfish on three shores, the gulls that eat both, the seals on the
skerries and the puffins beside them; on the hills above, the browse, the
fallow deer, wild goats and rabbits that graze it, the wolves and foxes that
hunt them, the harriers over the moor and the sparrowhawks in the wood, the
squirrels, the dragonflies over the pools, the Keep's cats, ponies and
alpacas — and the two companies that work the water every tide. The Ferrymen's Guild crosses on any tide and is owed for it. The
Crown's Warden writes down what the Guild will not say aloud.

    python3 sandbox/ecosystem.py                       # one tide-cycle, seed 1
    python3 sandbox/ecosystem.py --tides 84 --seed 7   # longer, elsewhere
    python3 sandbox/ecosystem.py --state .ecosystem-state.json   # keeps going between visits
    python3 sandbox/ecosystem.py --state .ecosystem-state.json --history   # the written past
    python3 sandbox/ecosystem.py --ledger              # the Warden's ledger, rings and all
    python3 sandbox/ecosystem.py --html sounds.html    # the chronicle as a page, for the site
    python3 sandbox/ecosystem.py --edition fourth      # Fourth Island, its own account
    python3 sandbox/ecosystem.py --edition sea         # the open sea, seen from a deck
    python3 sandbox/ecosystem.py --check               # the invariants hold, both editions

Standard library only: nothing installed, fetched, or executed from
elsewhere. The companies it names are read out of `index.html` through
`teller/questfile.py`, so the sandbox stands behind the same record as the
quest rather than keeping a second copy of it.

The world data at the top is the sandbox's own and is soft content in
WORLD.md's sense — bounded by the spine, owed nothing by any chapter. The
engine below it never needs editing to re-voice or re-stock the sandbox.

Three editions run on the same engine: the Sounds (the three islands, the
skerries, the ferry and the Warden, in the ferryman's voice), Fourth
Island (one island facing open sea, no ferry, no ledger, in an account a
hermit might have noticed), and the open sea beyond them all (plankton
and shoals, dolphins and whales, and the reef south of Fourth Island, as
seen from a deck). The Sounds edition lists Fourth Island and does not
simulate it: ferrymen do not point at it.
"""

from __future__ import annotations

import argparse
import datetime
import html
import json
import math
import os
import random
import re
import sys

# ============================================================
# WORLD DATA — the sandbox's own. CC BY 4.0, see CONTENT-LICENSE.md.
# Soft content: bounded by the spine in WORLD.md, contradicted freely
# by a better idea in a later chapter. Fourth Island's ground is written
# in WORLD.md and is its own edition here; the Sounds edition lists it
# and does not simulate it.
# ============================================================

TIDES_PER_CYCLE = 28   # two tides a day; springs a fortnight apart
YEAR_TIDES = 365 * 2   # two tides a day, and the springs keep their own count

# The seasons, by the first tide of each in the year (the year opens in
# winter; spring comes in on the first of March, summer on the first of
# June, autumn on the first of September), and what each does: the odds
# of the weather, how much the big tides stir the bloom, how fast the
# grazing, the shore and the wood grow, and how hard hunger bites.
SEASONS = [
    {"name": "winter", "from": 0,
     "weather": {"calm": 22, "fresh": 36, "blowing": 30, "storm": 12},
     "bloom": 0.4, "grow": 0.35, "starve": 1.2},
    {"name": "spring", "from": 59 * 2,
     "weather": {"calm": 30, "fresh": 40, "blowing": 22, "storm": 8},
     "bloom": 1.4, "grow": 1.3, "starve": 1.0},
    {"name": "summer", "from": 151 * 2,
     "weather": {"calm": 50, "fresh": 35, "blowing": 12, "storm": 3},
     "bloom": 1.0, "grow": 1.0, "starve": 0.8},
    {"name": "autumn", "from": 243 * 2,
     "weather": {"calm": 30, "fresh": 38, "blowing": 22, "storm": 10},
     "bloom": 0.8, "grow": 0.6, "starve": 1.0},
]

# Who does what in the biosphere. Each species below carries a role; the
# page groups them by it. The plants are named here because they are
# stocks rather than species.
ROLES = [
    ("grows",           "what everything else lives on"),
    ("feeds",           "on what grows"),
    ("pollinates",      "and sets the fruit"),
    ("hunts",           "and keeps the feeders in check"),
    ("picks up after",  "the hunters and the tide"),
    ("is kept",         "by the Keep, and fed when the hill is bare"),
]
PLANTS = {"the bloom": "sounds", "the grazing": "shore", "the wood": "shore",
          "the shore's shellfish beds": "shore", "the worms in the turf": "shore",
          "the berries": "shore", "the blossom": "shore", "the fruit": "shore",
          "the plankton": "sea", "the coral": "reef", "the rafts of sea trees": "sea"}

PLACES = {
    "sounds":   {"name": "the Sounds"},
    "first":    {"name": "First Island", "shore": True, "quay": True, "coves": True},
    "second":   {"name": "Second Island", "shore": True, "narrows": ["third"],
                 "coves": True, "caves": True},
    "third":    {"name": "Third Island", "shore": True, "narrows": ["second"],
                 "coves": True, "caves": True},
    "skerries": {"name": "the skerries between Second and Third"},
    "fourth":   {"name": "Fourth Island", "shore": True, "cliffs": True,
                 "coves": True, "caves": True},
    "sea":      {"name": "the open sea"},
    "reef":     {"name": "the reef south of Fourth Island"},
}

SPECIES = {
    # The herring live in the Sounds and feed on the bloom. When the
    # Sounds run thin, a new shoal comes in from the open sea on a spring
    # tide — herring are travellers, and the kingdom is on their road.
    "herring":   {"capacity": 12000, "rate": 0.6, "start": 6000, "shoal": 1500,
                  "thin_below": 1500, "role": "feeds"},
    # Shellfish on every written shore. They feed while the water is over
    # them, so the big tides suit them; spat settles on a bare shore at
    # the springs.
    "shellfish": {"capacity": 800, "rate": 0.15, "start": 500, "spat": 80,
                  "bare_below": 150, "roots": 50, "role": "feeds",
                  "breeds": ["spring", "summer"]},
    # Gulls nest on every written shore, fish the Sounds when the water
    # can be worked, turn to the shore when it cannot, and take the
    # scraps at First Island's quay. Fledging happens on the springs.
    "gulls":     {"start": {"first": 120, "second": 90, "third": 70, "fourth": 60},
                  "cap": 250, "need": 1.0, "herring_take": 0.7,
                  "shore_take": 0.4, "breed": 0.03, "breed_above": 0.7, "wear": 0.0005,
                  "hungry_below": 0.6, "starve": 0.02, "wander": 0.02,
                  "wander_told": 3, "role": "picks up after",
                  "breeds": ["spring", "summer"]},
    # Seals on the skerries, fishing the same herring.
    "seals":     {"start": 12, "cap": 24, "fish_each": 4, "short": 0.2,
                  "role": "hunts", "breeds": ["autumn"]},
    # The hills: the grazing on every written island — browse, in the
    # keeper's word, which is the key here and never the reader's word,
    # since on a page it reads as a verb — eaten by the deer, the goats
    # and the rabbits. Nothing grazes below the roots, and a stripped
    # hill regrows from them, slowly.
    "browse":    {"capacity": 6000, "rate": 0.05, "start": 4000, "roots": 300,
                  "bare_below": 500},
    # Fallow deer on every written island, fawning when the hill feeds
    # them. First Island's are the Keep's to hunt, in fair weather, and
    # the Keep's huntsmen are that island's wolves. A few deer, a few
    # rabbits and a fox or two always survive: hills have corners.
    "deer":      {"start": {"first": 30, "second": 60, "third": 60},
                  "cap": 120, "need": 0.5, "breed": 0.012, "wear": 0.001,
                  "hungry_below": 1.0, "starve": 0.15, "remnant": 5, "hunt_above": 15,
                  "hunted": 0.012, "table_told": 0.3, "role": "feeds",
                  "breeds": ["spring", "summer"]},
    # Wolves, in packs, on the two islands with narrows between them. A
    # pack that dies out is replaced from across the narrows at a calm
    # neap, when the water between is narrowest.
    "wolves":    {"start": {"second": 3, "third": 3}, "cap": 8, "hunt": 0.03,
                  "need": 0.05, "easy_above": 20, "breed": 0.02, "short": 0.03,
                  "cross_from": 6, "crossing": 2, "role": "hunts",
                  "breeds": ["spring"]},
    # Rabbits on every written island, grazing the same hill as the deer
    # and breeding the way rabbits do.
    "rabbits":   {"start": {"first": 120, "second": 100, "third": 90, "fourth": 80},
                  "cap": 400, "need": 0.03, "breed": 0.04, "wear": 0.003,
                  "hungry_below": 0.6, "starve": 0.2, "remnant": 10, "many_above": 300,
                  "thin_below": 60, "role": "feeds",
                  "breeds": ["spring", "summer", "autumn"]},
    # Squirrels in the wood on every written island, living off the
    # wood itself; a storm shakes the nuts down and they do well after.
    "squirrels": {"start": {"first": 50, "second": 60, "third": 45, "fourth": 30},
                  "cap": 150, "rate": 0.01, "wear": 0.001, "windfall": 0.03,
                  "mast": "autumn", "role": "feeds"},
    # Foxes on every written island: rabbits first, squirrels when they
    # can get them, the quay's scraps on First Island. They cross the
    # narrows the way the wolves do.
    "foxes":     {"start": {"first": 4, "second": 5, "third": 4}, "cap": 10,
                  "hunt": 0.12, "hunt_squirrels": 0.02, "need": 0.1,
                  "easy_above": 150, "breed": 0.015, "short": 0.05, "remnant": 2,
                  "cross_from": 6, "crossing": 2, "role": "picks up after",
                  "breeds": ["spring"]},
    # Cats at the Keep and the quay on First Island, kept rather than
    # wild: fed enough by the kitchens never to starve, hunting anyway.
    "cats":      {"start": {"first": 12}, "cap": 24, "kept": 8,
                  "hunt": 0.05, "hunt_squirrels": 0.02, "hunt_birds": 0.04, "need": 0.04,
                  "easy_above": 100, "breed": 0.03, "wear": 0.002,
                  "short": 0.1, "role": "is kept", "breeds": ["spring", "summer"]},
    # Wild goats on every written island. They graze the hill with the
    # deer, but the crags feed them what the hill does not — the sandbox
    # does not count crag-browse, only that goats always find some — and
    # the wolves take one now and then.
    "goats":     {"start": {"first": 8, "second": 14, "third": 16, "fourth": 12}, "cap": 40,
                  "need": 0.3, "crags": 0.6, "breed": 0.012, "wear": 0.001,
                  "hungry_below": 0.8, "starve": 0.15, "remnant": 3,
                  "role": "feeds", "breeds": ["spring"]},
    # Puffins on the skerries, fishing the same herring as everything
    # else, fledging on the springs when the fishing has been good.
    "puffins":   {"start": 40, "cap": 200, "take": 0.3, "need": 0.3,
                  "breed": 0.06, "breed_above": 0.8, "wear": 0.001,
                  "hungry_below": 0.3, "starve": 0.05, "role": "hunts",
                  "breeds": ["summer"], "away": ["winter"]},
    # Dragonflies over the pools on every written island: a calm spell
    # hatches them, a storm knocks them down, and the pools always hold
    # a few more.
    "dragonflies": {"start": 30, "cap": 300, "hatch": 0.35, "seed": 5,
                    "blown": {"calm": 0.0, "fresh": 0.02, "blowing": 0.1,
                              "storm": 0.5},
                    "many_above": 150, "role": "hunts",
                    "breeds": ["spring", "summer"]},
    # Two hunters of the small things, one over the moor and one in the
    # wood. Each lives on one prey the sandbox counts and on the small
    # birds and voles it does not, and fledges on the springs when fed.
    "harriers":  {"start": {"second": 3, "third": 3, "fourth": 2}, "cap": 8, "prey": "rabbits",
                  "hunt": 0.03, "base": 0.015, "need": 0.04, "easy_above": 150,
                  "breed": 0.05, "short": 0.1, "remnant": 1, "role": "hunts",
                  "breeds": ["summer"]},
    "sparrowhawks": {"start": {"first": 2, "second": 2, "third": 2, "fourth": 1}, "cap": 6,
                     "prey": "small birds", "hunt": 0.05, "base": 0.005, "need": 0.05,
                     "easy_above": 300, "breed": 0.05, "short": 0.1, "remnant": 1,
                     "role": "hunts", "breeds": ["summer"]},
    # The Keep's stock on First Island, kept like the cats: they graze the
    # hill when it has grazing and eat the Keep's hay when it does not.
    # Small birds in the hedges and the wood on every written island, on the
    # worms in the turf all year and the berries the wood sets in autumn.
    # What the sparrowhawks and the cats are really for.
    "small birds": {"start": {"first": 200, "second": 220, "third": 180, "fourth": 150},
                    "cap": 600, "need": 0.1, "breed": 0.03, "wear": 0.001,
                    "hungry_below": 0.5, "starve": 0.05, "role": "feeds",
                    "breeds": ["spring", "summer"]},
    # The worms in the turf: a stock that follows the soil's season, and
    # comes up in wet weather more than dry.
    "worms":     {"capacity": 6000, "start": 4000, "rate": 0.08,
                  "up": {"calm": 0.5, "fresh": 1.0, "blowing": 0.8, "storm": 0.3}},
    # The berries: the wood sets them through late summer and autumn, the
    # birds strip them, and winter takes what is left.
    "berries":   {"capacity": 1500, "set": 40, "ripen": ["autumn"],
                  "keeps": ["autumn", "winter"], "fade": 0.05},
    # The open sea. The plankton is the sea's bloom; the shoals feed on it
    # and are too many to count; the dolphins live on the shoals; the whales
    # come in for the plankton in summer and autumn and go, nobody knowing
    # where, for the rest of the year. South of Fourth Island, in shallower
    # water, the coral grows in the warm seasons and breaks in storms, and
    # the reef fish live on it.
    "shoals":    {"capacity": 40000, "rate": 0.5, "start": 20000, "thin_below": 6000,
                  "run": 8000, "lives": "sea", "role": "feeds"},
    "dolphins":  {"start": 24, "cap": 60, "fish_each": 12, "need": 12,
                  "easy_above": 10000, "breed": 0.02, "short": 0.03,
                  "lives": "sea", "role": "hunts", "breeds": ["summer"]},
    "whales":    {"start": 6, "cap": 16, "need": 40, "breed": 0.01, "short": 0.01,
                  "lives": "sea", "role": "feeds", "breeds": ["autumn"],
                  "away": ["winter", "spring"]},
    "coral":     {"capacity": 5000, "start": 3000, "rate": 0.006,
                  "warm": ["summer", "autumn"], "storm_break": 0.02,
                  "broke_told": 90},
    "reef fish": {"start": 800, "per_coral": 0.5, "rate": 0.03, "wear": 0.001,
                  "lives": "reef", "role": "feeds", "breeds": ["spring", "summer"]},
    # Blossom on the hills in spring and summer; bees in it, which set the
    # fruit; fruit in the woods in autumn, as much as the bees made. The
    # deer, the squirrels and the small birds eat it, and so do the Keep's
    # people and the hermits.
    "flowers":   {"capacity": 2000, "set": 40, "seasons": ["spring", "summer"],
                  "fade": 0.08},
    "bees":      {"start": {"first": 20, "second": 24, "third": 18, "fourth": 10},
                  "cap": 60, "need": 20, "breed": 0.04, "storm_loss": 0.01,
                  "full_at": 30, "role": "pollinates", "breeds": ["spring", "summer"],
                  "away": ["winter"]},
    "fruit":     {"capacity": 1500, "set": 60, "ripen": ["autumn"], "poor_below": 0.5},
    # Fishing eagles: a pair or two on every written island, fishing the
    # Sounds and the water off the cliffs.
    "fishing eagles": {"start": {"first": 1, "second": 2, "third": 2, "fourth": 2},
                       "cap": 4, "fish_each": 3, "need": 3, "breed": 0.02,
                       "short": 0.01, "role": "hunts", "breeds": ["summer"]},
    # Rafts of floating sea trees form on the open sea in the warm seasons,
    # drift, shelter fish, and break up in storms; and the sea ostriches —
    # big flightless birds that live on the rafts, dive for fish, nest on
    # the rafts and cannot land on the islands — ride them.
    "rafts":     {"start": 6, "cap": 40, "form": 0.16,
                  "seasons": ["summer", "autumn"],
                  "break": 0.06, "sink": 0.002, "broke_told": 2},
    "sea ostriches": {"start": 30, "cap": 120, "fish_each": 4, "need": 4,
                      "per_raft": 8, "breed": 0.05, "storm_loss": 0.005,
                      "lives": "sea", "role": "hunts",
                      "breeds": ["summer", "autumn"]},
    "ponies":    {"start": {"first": 8}, "cap": 14, "kept": 6, "need": 0.6,
                  "hay": 0.7, "breed": 0.01, "wear": 0.002, "role": "is kept",
                  "breeds": ["spring"]},
    "alpacas":   {"start": {"first": 12}, "cap": 24, "kept": 10, "need": 0.25,
                  "hay": 0.7, "breed": 0.012, "wear": 0.002, "role": "is kept",
                  "breeds": ["spring", "summer"]},
}

# Who crosses the narrows, and what the chronicle says when they do.
CROSSERS = [("wolves", "crossed"), ("foxes", "fox_crossed")]
# The hunters of small things, and the lines for them.
HUNTERS = [("harriers", "harrier_fledged", "harriers_short"),
           ("sparrowhawks", "hawk_fledged", "hawks_short")]
# The Keep's kept grazers, and the line for each new one.
KEPT = [("ponies", "foal"), ("alpacas", "cria")]

WEATHER = [("calm", 35), ("fresh", 40), ("blowing", 18), ("storm", 7)]
BLOOM_LEVEL = 60       # the bloom in an ordinary season; each season scales it
WORKABLE = {"calm": 1.0, "fresh": 0.8, "blowing": 0.4, "storm": 0.0}
ABOARD = {"calm": (1, 4), "fresh": (1, 3), "blowing": (0, 2), "storm": (0, 1)}
FARE_IN_NEWS = 0.3     # how often a passenger has news the ferryman hasn't got
SCRAPS_EACH = 2        # what a passenger leaves the quay's gulls
CATCH_SHARE = 0.04     # what First Island's boats take of the herring
CATCH_MOST = 150       # ...and the most they can land in one tide
# gathered at the quay island per tide — never more than a tenth of the shore
GATHERING = {"calm": 30, "fresh": 15, "blowing": 0, "storm": 0}
GOOD_CATCH = 130

# The companies the sandbox stands behind, by their keys in index.html.
COMPANIES_ON_THE_WATER = ["guild", "crown"]

# What a kill leaves for the scavengers, in the units they eat: a deer or
# a goat left by the wolves feeds gulls (in fish) and foxes (in rabbits)
# on the next tide.
CARRION = {"gulls": 30, "foxes": 20, "goat": 0.4}

# The hermits of Fourth Island: a presence, never a count. Sailors — some
# came ashore by choice, some the sea put there — who gather on the shore
# in fair weather and take a goat now and then (WORLD.md). Now and then
# one more arrives, or is stranded; the account says so and counts nobody.
HERMITS = {"island": "fourth",
           "gathering": {"calm": 8, "fresh": 4, "blowing": 0, "storm": 0},
           "goat": 0.005, "smoke": 0.15, "arrived": 0.006, "stranded": 0.03}

# What the chronicle says. The engine fills the braces and joins the
# clauses; every word a player reads is here.
LINES = {
    "tide":        "Tide {tide} · {season} · {label} · {weather} — {clauses}.",
    "season_turn": "{season} came in",
    "carrion":     "gulls on the wolves' kill on {place}",
    "quiet":       "nothing else worth a fare",
    "storm":       "a storm went through the Sounds",
    "shoal":       "a new shoal came into the Sounds on the flood",
    "thin":        "the herring thinned",
    "back":        "the herring came back",
    "fledged":     "gulls fledged on {place}",
    "fledged_all": "gulls fledged on every shore",
    "hungry":      "gulls went hungry on {place}",
    "hungry_all":  "gulls went hungry on every shore",
    "failed":      "the last gulls left {place}",
    "returned":    "gulls settled {place} again",
    "south":       "some gulls went south, and no ferryman looked after them",
    "north":       "gulls came back from the south, and no ferryman asked "
                   "where from",
    "pup":         "a pup on the skerries",
    "seals_short": "the seals went short",
    "haul_out":    "the seals hauled out at low water",
    "bare":        "the deer have stripped the hill on {place}",
    "greened":     "the hill greened again on {place}",
    "deer_hungry": "the fallow deer went hungry on {place}",
    "deer_hungry_all": "the fallow deer went hungry on every hill",
    "table":       "a deer for the Keep's table",
    "cub":         "a cub in the pack on {place}",
    "wolves_short": "the wolves went short on {place}",
    "last_wolf":   "the last wolf left {place}",
    "crossed":     "wolves crossed the narrows to {place}",
    "fox_crossed": "foxes crossed the narrows to {place}",
    "rabbits_many": "rabbits everywhere on {place}",
    "rabbits_thin": "the rabbits thinned on {place}",
    "fox_cubs":    "fox cubs in the earth on {place}",
    "foxes_short": "the foxes went short on {place}",
    "kittens":     "kittens at the Keep",
    "cats_short":  "the Keep's cats went hungry, and the kitchens noticed",
    "windfall":    "the storm shook the nuts down on {place}",
    "windfall_all": "the storm shook the nuts down in every wood",
    "kid":         "kids on the crags on {place}",
    "goats_hungry": "the goats went hungry on {place}",
    "puffins_fledged": "puffins fledged on the skerries",
    "puffins_hungry": "the puffins went hungry",
    "dragonflies": "dragonflies over the pools on {place}",
    "dragonflies_all": "dragonflies over every pool in the kingdom",
    "harrier_fledged": "a harrier fledged over the moor on {place}",
    "harriers_short": "the harriers went short on {place}",
    "hawk_fledged": "a sparrowhawk fledged in the wood on {place}",
    "hawks_short":  "the sparrowhawks went short on {place}",
    "foal":        "a foal in the Keep's stable",
    "cria":        "a cria among the Keep's alpacas",
    "catch":       "a good catch landed at {place}",
    "ferry":       "the ferry crossed with {aboard} aboard",
    "ferry_empty": "the ferry crossed empty, and is owed for it",
    "ferry_storm": "the ferry crossed anyway",
    "in_news":     "{n} paying in news",
    "numbers":     ["no", "one", "two", "three", "four", "five", "six"],
    "companies":   "On the water: {name} — {quest}",
    "own_account": "not simulated here — it keeps its own account",
    "off_record":  "off the record, somewhere south",
    "gathered":    "Gathered on the shore: {n} shellfish.",
    "hermits_goat": "a goat for the hermits' pot",
    "smoke":       "smoke on the hill",
    "arrived":     "a sail off the south, and then a boat on the stones, and "
                   "nobody putting out again",
    "stranded":    "the sea put somebody ashore in the night",
    "berries":     "berries in the wood on {place}",
    "berries_all": "berries in every wood",
    "in_berries":  "the small birds were in the berries on {place}",
    "in_berries_all": "the small birds were in the berries everywhere",
    "birds_hungry": "the small birds went hungry on {place}",
    "birds_hungry_all": "the small birds went hungry on every island",
    "blossom":     "blossom on the hill on {place}",
    "blossom_all": "blossom on every hill",
    "bees":        "bees in the blossom on {place}",
    "bees_all":    "bees in the blossom everywhere",
    "fruit":       "fruit in the wood on {place}",
    "fruit_all":   "fruit in every wood",
    "poor_fruit":  "a poor fruit year on {place}",
    "poor_fruit_all": "a poor fruit year everywhere",
    "eagle":       "an eagle over the Sound with a fish",
    "eaglets":     "eaglets on {place}",
    "cove_fry":    "fry in the cove at low water on {place}",
    "cove_fry_all": "fry in every cove at low water",
    "caves":       "the seals were in the caves",
    "raft":        "a raft of sea trees drifting west",
    "rafts_broke": "the storm broke up the rafts",
    "ostriches":   "sea ostriches standing on a raft as it went by",
    "ostrich_chicks": "chicks among the sea ostriches on the rafts",
    "ostriches_short": "the sea ostriches went short",
    "whales_back":  "the whales came back",
    "whales_gone":  "the whales went, wherever they go",
    "whales_blow":  "whales blowing to the south",
    "calf":         "a calf among the whales",
    "whales_short": "the whales went short",
    "dolphins":     "dolphins at the bow",
    "dolphins_born": "young among the dolphins",
    "dolphins_short": "the dolphins went short",
    "shoal_silver": "the sea was silver with a shoal",
    "shoals_thin":  "the shoals thinned",
    "shoals_run":   "a run of fish came up from the south",
    "reef_broke":   "the storm broke coral on the reef",
    "reef_showing": "the reef showing at low water",
    "reef_fish":    "the reef thick with fish",
}

# The chronicle as a page. The engine fills the braces; the words are here.
PAGE = {
    "title":    "The Sounds",
    "kicker":   "The Kingdom of the Four Sounds",
    "lede":     "One tide-cycle of the waters the kingdom is named for, "
                "ticked over on {date}. The chronicle is the ferryman's: one "
                "line a tide, what happened and whether it was worth a fare. "
                "The Warden's ledger is kept and not shown — the bell is not "
                "counted aloud.",
    "chronicle": "The chronicle",
    "roles":    "Who does what",
    "after":    "After the cycle",
    "back":     "Back to the quest",
    "foot":     "A mini ecosystem, run again each day from the repository's "
                "sandbox; the same day gives the same Sounds to everyone.",
    "links":    [["Fourth Island, which nobody points at", "../fourth/"],
                 ["The open sea", "../sea/"]],
}

# Editions: which places the run holds, whether the ferry and the Warden
# run, whether the skerries are in it, and the words that differ. The
# engine reads these and adds nothing.
EDITIONS = {
    "sounds": {
        "places": ["sounds", "first", "second", "third", "skerries", "fourth"],
        "unsimulated": ["fourth"],   # ferrymen do not point at it
        "ferry": True, "skerries": True, "lines": {}, "page": {},
    },
    "fourth": {
        "places": ["sounds", "fourth"],   # the Sounds end on its northern shore
        "unsimulated": [],
        "ferry": False, "skerries": False,
        "lines": {
            "quiet":       "nothing anyone would tell",
            "quiet_pool":  ["nothing anyone would tell",
                            "the tide came up the stones and went down again",
                            "gulls on the cliffs, and the sea beyond them",
                            "the goats were on the crags at low water",
                            "rabbits out on the hill at dusk",
                            "a hawk over the wood, once",
                            "the pools were still",
                            "the wood was loud with the wind"],
            "storm":       "a storm came over the hill",
            "fledged":     "gulls fledged on the cliffs",
            "hungry":      "gulls went hungry on the cliffs",
            "failed":      "the last gulls left the cliffs",
            "returned":    "gulls settled the cliffs again",
            "south":       "some gulls went off over the sea, and nobody followed them",
            "north":       "gulls came in off the sea, from wherever they had been",
            "off_record":  "off over the sea, somewhere",
            "bare":        "the goats and the rabbits have stripped the hill",
            "greened":     "the hill greened again",
            "rabbits_many": "rabbits everywhere on the hill",
            "rabbits_thin": "the rabbits thinned",
            "goats_hungry": "the goats went hungry",
            "kid":         "kids on the crags",
            "windfall":    "the storm shook the nuts down in the wood",
            "harrier_fledged": "a harrier fledged over the hill",
            "harriers_short": "the harriers went short",
            "hawk_fledged": "a sparrowhawk fledged in the wood",
            "hawks_short": "the sparrowhawks went short",
            "dragonflies": "dragonflies over the pools",
            "carrion":     "gulls on a kill on the hill",
            "blossom":     "blossom on the hill",
            "bees":        "bees in the blossom",
            "fruit":       "fruit in the wood",
            "poor_fruit":  "a poor fruit year",
            "eagle":       "an eagle off the cliffs with a fish",
            "eaglets":     "eaglets on the cliffs",
            "cove_fry":    "fry in the cove at low water",
            "caves":       "the sea was loud in the caves",
            "berries":     "berries in the wood",
            "in_berries":  "the small birds were in the berries",
            "birds_hungry": "the small birds went hungry",
        },
        "page": {
            "title":    "Fourth Island",
            "lede":     "One tide-cycle of Fourth Island, which the ferrymen do "
                        "not point at, ticked over on {date}. Nobody there "
                        "keeps a ledger or counts a tide aloud; the kingdom's "
                        "tide-calendar is borrowed for the numbering, and the "
                        "account is what a hermit might have noticed. The "
                        "record follows the gulls this far and no further.",
            "foot":     "A mini ecosystem, run again each day from the "
                        "repository's sandbox; the same day gives the same "
                        "island to everyone.",
            "links":    [["The Sounds", "../sounds/"], ["The open sea", "../sea/"]],
        },
    },
    "sea": {
        "places": ["sea", "reef"],
        "unsimulated": [],
        "ferry": False, "skerries": False,
        "lines": {
            "quiet":       "nothing anyone would tell",
            "quiet_pool":  ["nothing anyone would tell",
                            "flat calm to the edge of the world",
                            "a swell from the south, and nothing on it",
                            "the sea and the sky and the line between them",
                            "spray over the bow all the tide",
                            "gulls far out, then none",
                            "a long light on the water going west"],
            "storm":       "a storm, and the sea standing up",
        },
        "page": {
            "title":    "The Open Sea",
            "lede":     "One tide-cycle of the open sea beyond the islands, "
                        "ticked over on {date}, as seen from a deck. Nobody "
                        "keeps an account out here; this is what a sailor might "
                        "have told, had a sailor come in. The rest of the known "
                        "world is this.",
            "foot":     "A mini ecosystem, run again each day from the "
                        "repository's sandbox; the same day gives the same sea "
                        "to everyone.",
            "links":    [["The Sounds", "../sounds/"], ["Fourth Island", "../fourth/"]],
        },
    },
}

# ============================================================
# ENGINE — MIT, see LICENSE. Reads the data above; adds no words.
# ============================================================

_BASE_LINES = dict(LINES)
_BASE_PAGE = dict(PAGE)
EDITION = "sounds"
SHORES: list[str] = []
QUAY: str | None = None
FERRY = True
SKERRIES = True
AT_SEA = False
IN_SOUNDS = True


def configure(edition: str) -> None:
    """Point the engine at one edition: its shores, its quay if any, whether
    the ferry and the skerries are in it, and its words."""
    global EDITION, SHORES, QUAY, FERRY, SKERRIES, AT_SEA, IN_SOUNDS, LINES, PAGE
    ed = EDITIONS[edition]
    EDITION = edition
    SHORES = [k for k in ed["places"]
              if PLACES[k].get("shore") and k not in ed["unsimulated"]]
    QUAY = next((k for k in SHORES if PLACES[k].get("quay")), None)
    FERRY = ed["ferry"]
    SKERRIES = ed["skerries"]
    AT_SEA = "sea" in ed["places"]
    IN_SOUNDS = "sounds" in ed["places"]
    LINES = {**_BASE_LINES, **ed["lines"]}
    PAGE = {**_BASE_PAGE, **ed["page"]}


configure("sounds")


def tide_range(t: int) -> float:
    """0 at the neaps, 1 at the springs, and back again every cycle."""
    return 0.5 + 0.5 * math.cos(2 * math.pi * t / TIDES_PER_CYCLE)


def tide_label(r: float) -> str:
    """The springs, the neaps, and the middling tides between — the
    sailors' words, plural, so a season called spring is never a tide."""
    return "springs" if r > 0.85 else "neaps" if r < 0.15 else "middling"


def season_for(abs_tide: int) -> dict:
    t = abs_tide % YEAR_TIDES
    current = SEASONS[-1]
    for season in SEASONS:
        if t >= season["from"]:
            current = season
    return current


def in_season(spec: dict, season: str) -> bool:
    """Whether a species breeds in this season; one with no season listed
    breeds in any."""
    return season in spec.get("breeds", [season])


def year_tide_for(date: datetime.date) -> int:
    """The tide of the year a date falls on: two a day, from the first."""
    return min((date.timetuple().tm_yday - 1) * 2, YEAR_TIDES - 1)


def rng_for(seed: int, tide: int) -> random.Random:
    """One stream per tide, so a run continued from a saved state is the
    same run as one played straight through — the written stays written."""
    return random.Random(f"{seed}:{tide}")


def fresh_state(seed: int, edition: str = "sounds", year_tide: int = 0) -> dict:
    configure(edition)
    g = SPECIES["gulls"]
    return {
        "seed": seed,
        "edition": edition,
        "tide": 0,
        "year_tide": year_tide,   # where in the year the run begins
        "bloom": 50,
        "herring": SPECIES["herring"]["start"] if IN_SOUNDS else 0,
        "shellfish": {k: SPECIES["shellfish"]["start"] for k in SHORES},
        "gulls": {k: g["start"].get(k, 0) for k in SHORES},
        "seals": SPECIES["seals"]["start"] if SKERRIES else 0,
        "browse": {k: SPECIES["browse"]["start"] for k in SHORES},
        "deer": {k: SPECIES["deer"]["start"].get(k, 0) for k in SHORES},
        "wolves": {k: SPECIES["wolves"]["start"].get(k, 0) for k in SHORES},
        "rabbits": {k: SPECIES["rabbits"]["start"].get(k, 0) for k in SHORES},
        "squirrels": {k: SPECIES["squirrels"]["start"].get(k, 0) for k in SHORES},
        "foxes": {k: SPECIES["foxes"]["start"].get(k, 0) for k in SHORES},
        "cats": {k: SPECIES["cats"]["start"].get(k, 0) for k in SHORES},
        "goats": {k: SPECIES["goats"]["start"].get(k, 0) for k in SHORES},
        "dragonflies": {k: SPECIES["dragonflies"]["start"] for k in SHORES},
        "harriers": {k: SPECIES["harriers"]["start"].get(k, 0) for k in SHORES},
        "sparrowhawks": {k: SPECIES["sparrowhawks"]["start"].get(k, 0)
                         for k in SHORES},
        "ponies": {k: SPECIES["ponies"]["start"].get(k, 0) for k in SHORES},
        "alpacas": {k: SPECIES["alpacas"]["start"].get(k, 0) for k in SHORES},
        "puffins": SPECIES["puffins"]["start"] if SKERRIES else 0,
        "plankton": 50,
        "shoals": SPECIES["shoals"]["start"] if AT_SEA else 0,
        "dolphins": SPECIES["dolphins"]["start"] if AT_SEA else 0,
        "whales": SPECIES["whales"]["start"] if AT_SEA else 0,
        "coral": SPECIES["coral"]["start"] if AT_SEA else 0,
        "reef fish": SPECIES["reef fish"]["start"] if AT_SEA else 0,
        "south": 0,
        "gathered": 0,
        "carrion": {k: 0.0 for k in SHORES},
        "small birds": {k: SPECIES["small birds"]["start"].get(k, 0) for k in SHORES},
        "worms": {k: SPECIES["worms"]["start"] for k in SHORES},
        "berries": {k: 0 for k in SHORES},
        "flowers": {k: 0 for k in SHORES},
        "bees": {k: SPECIES["bees"]["start"].get(k, 0) for k in SHORES},
        "fruit": {k: 0 for k in SHORES},
        "pollination": {k: [0.0, 0] for k in SHORES},   # summed index, tides
        "fishing eagles": {k: SPECIES["fishing eagles"]["start"].get(k, 0) for k in SHORES},
        "rafts": SPECIES["rafts"]["start"] if AT_SEA else 0,
        "sea ostriches": SPECIES["sea ostriches"]["start"] if AT_SEA else 0,
        "gathered_fruit": 0,
        "flags": {"thin": False, "hungry": {k: False for k in SHORES},
                  "bare": {k: False for k in SHORES},
                  "deer_hungry": {k: False for k in SHORES},
                  "rabbits_many": {k: False for k in SHORES},
                  "rabbits_thin": {k: False for k in SHORES},
                  "goats_hungry": {k: False for k in SHORES},
                  "birds_hungry": {k: False for k in SHORES},
                  "shoals_thin": False,
                  "blossom_told": {k: False for k in SHORES},
                  "bees_told": {k: False for k in SHORES},
                  "fruit_told": {k: False for k in SHORES},
                  "fry_told": {k: False for k in SHORES},
                  "whales_home": season_for(year_tide)["name"] not in SPECIES["whales"]["away"],
                  "berries_told": {k: False for k in SHORES},
                  "in_berries_told": {k: False for k in SHORES},
                  "dragonflies": {k: False for k in SHORES},
                  "puffins_hungry": False},
        "guild": {"crossings": 0, "coin": 0, "news": 0, "empty": 0},
        "landed": 0,
        "warden": [],       # [tide, rings, aboard, landed] — never said aloud
        "chronicle": [],
    }


def clamp(n: int, lo: int, hi: int) -> int:
    return max(lo, min(hi, n))


def rounded(x: float, rng: random.Random) -> int:
    """A fractional count becomes a whole one by lot: 0.3 of a kill is a
    kill three tides in ten, not never."""
    whole = int(x)
    return whole + (1 if rng.random() < x - whole else 0)


def words(n: int) -> str:
    """Small counts in words, as a ferryman would say them."""
    names = LINES["numbers"]
    return names[n] if 0 <= n < len(names) else str(n)


def step(state: dict) -> str:
    """Advance one tide. Returns the chronicle line, which is also kept."""
    t = state["tide"]
    rng = rng_for(state["seed"], t)
    abs_tide = state["year_tide"] + t
    r = tide_range(abs_tide)
    label = tide_label(r)
    season = season_for(abs_tide)
    sn = season["name"]
    weather = rng.choices(list(season["weather"]), list(season["weather"].values()))[0]
    work = WORKABLE[weather]
    spring = label == "springs"
    grow, starve = season["grow"], season["starve"]
    events: list[str] = []
    flags = state["flags"]

    if abs_tide % YEAR_TIDES == season["from"]:
        events.append(LINES["season_turn"].format(season=sn))
    if weather == "storm":
        events.append(LINES["storm"])

    # -- the bloom: settles toward the season's level, stirred up by the
    #    big tides and by storms ----------------------------------------
    level = BLOOM_LEVEL * season["bloom"]
    stir = int(12 * (r - 0.5)) + (10 if weather == "storm" else 0)
    bloom = state["bloom"] + int((level - state["bloom"]) * 0.1) + stir
    state["bloom"] = clamp(bloom, 0, 100)
    catch = gull_fish = seal_fish = puffin_fish = 0

    if AT_SEA:
        sea_events(state, rng, sn, season, r, weather, spring, stir, events)

    # -- herring: grow on the bloom, then everything eats them --------
    hs = SPECIES["herring"]
    h = state["herring"] if IN_SOUNDS else 0
    h += int(hs["rate"] * (state["bloom"] / 100) * h * (1 - h / hs["capacity"]))
    if weather == "storm":
        h -= h // 20
    gulls = state["gulls"]
    total_gulls = sum(gulls.values())
    gs = SPECIES["gulls"]
    gull_fish = min(h, int(total_gulls * gs["herring_take"] * work))
    h -= gull_fish
    ss = SPECIES["seals"]
    seal_fish = (min(h, int(state["seals"] * ss["fish_each"] * max(work, 0.5)))
                 if SKERRIES else 0)
    h -= seal_fish
    ps = SPECIES["puffins"]
    puffin_fish = (min(h, state["puffins"] * ps["take"] * work)
                   if SKERRIES and sn not in ps["away"] else 0)
    h -= int(puffin_fish)
    es = SPECIES["fishing eagles"]
    eagle_fish = min(h, int(sum(state["fishing eagles"].values()) * es["fish_each"] * work))
    h -= eagle_fish
    catch = min(h, int(h * CATCH_SHARE * work), CATCH_MOST) if QUAY else 0
    h -= catch
    state["landed"] += catch
    if catch >= GOOD_CATCH:
        events.append(LINES["catch"].format(place=PLACES[QUAY]["name"]))
    shoal = IN_SOUNDS and flags["thin"] and spring and h < hs["thin_below"]
    if shoal:
        h += hs["shoal"]
        events.append(LINES["shoal"])
    thin = IN_SOUNDS and h < hs["thin_below"]
    if thin and not flags["thin"]:
        events.append(LINES["thin"])
    elif flags["thin"] and not thin and not shoal:
        events.append(LINES["back"])
    flags["thin"] = thin
    if IN_SOUNDS:
        state["herring"] = h
    else:
        state["landed"] = 0

    # -- the ferry: on any tide, and owed for it (where there is one) --
    aboard = in_news = scraps = 0
    if FERRY:
        lo, hi = ABOARD[weather]
        aboard = rng.randint(lo, hi)
        guild = state["guild"]
        guild["crossings"] += 1
        for _ in range(aboard):
            if rng.random() < FARE_IN_NEWS:
                in_news += 1
            else:
                guild["coin"] += 1
        guild["news"] += in_news
        if aboard == 0:
            guild["empty"] += 1
        scraps = aboard * SCRAPS_EACH

    # -- shores: shellfish feed, gulls feed, First Island gathers -----
    shs = SPECIES["shellfish"]
    shell = state["shellfish"]
    fledged: list[str] = []
    newly_hungry: list[str] = []
    for place in SHORES:
        g = gulls[place]
        s = shell[place]
        s += int(shs["rate"] * season["bloom"] * (0.5 + r) * s * (1 - s / shs["capacity"]))
        if weather == "storm":
            s -= s // 20
        shore_take = 0 if weather == "storm" else min(
            max(0, s - shs["roots"]), int(g * gs["shore_take"] * (1.2 - work)))
        s -= shore_take
        open_bed = max(0, s - shs["roots"])
        if place == QUAY:
            gathered = min(open_bed // 10, GATHERING[weather])
        elif place == HERMITS["island"]:
            gathered = min(open_bed // 10, HERMITS["gathering"][weather])
        else:
            gathered = 0
        s -= gathered
        state["gathered"] += gathered
        if s < shs["bare_below"] and spring and in_season(shs, sn):
            s += shs["spat"]
        shell[place] = max(0, s)

        fish_share = gull_fish * g // total_gulls if total_gulls else 0
        carrion = state["carrion"][place]
        picked = min(carrion * CARRION["gulls"], g * gs["need"]) if g else 0
        if picked and rng.random() < 0.3:
            events.append(LINES["carrion"].format(place=PLACES[place]["name"]))
        fed_on = fish_share + shore_take + picked + (scraps if place == QUAY else 0)
        fed = fed_on / (g * gs["need"]) if g else 1.0
        born = 0
        if g and fed >= gs["breed_above"] and spring and in_season(gs, sn) and g < gs["cap"]:
            born = max(1, int(g * gs["breed"]))
            fledged.append(place)
        lost = int(g * gs["wear"])
        hungry = bool(g) and fed < gs["hungry_below"]
        if hungry:
            lost += rounded(g * (gs["hungry_below"] - fed) * gs["starve"] * starve, rng)
            if not flags["hungry"][place]:
                newly_hungry.append(place)
        flags["hungry"][place] = hungry
        new_g = max(0, g - lost + born)
        if g and not new_g:
            events.append(LINES["failed"].format(place=PLACES[place]["name"]))
        gulls[place] = new_g
    for places, one, every in ((fledged, "fledged", "fledged_all"),
                               (newly_hungry, "hungry", "hungry_all")):
        if len(places) == len(SHORES) > 1:
            events.append(LINES[every])
        else:
            events.extend(LINES[one].format(place=PLACES[k]["name"]) for k in places)

    # -- gulls move: empty shores resettle; some go off the record ----
    if weather == "calm" and SHORES:
        biggest = max(SHORES, key=lambda k: gulls[k])
        for place in SHORES:
            if gulls[place] == 0 and gulls[biggest] >= 20:
                gulls[biggest] -= 10
                gulls[place] = 10
                events.append(LINES["returned"].format(place=PLACES[place]["name"]))
        back = state["south"] // 2
        if back:
            state["south"] -= back
            gulls[biggest] += back
            if back >= gs["wander_told"]:
                events.append(LINES["north"])
        if spring:
            away = rounded(sum(gulls.values()) * gs["wander"], rng)
            away = min(away, gulls[biggest])
            if away:
                gulls[biggest] -= away
                state["south"] += away
                if away >= gs["wander_told"]:
                    events.append(LINES["south"])

    # -- seals -------------------------------------------------------
    seals = state["seals"]
    if seals and SKERRIES:
        fed = seal_fish / (seals * ss["fish_each"])
        if (fed >= 0.9 and spring and in_season(ss, sn) and seals < ss["cap"]
                and rng.random() < 0.5):
            seals += 1
            events.append(LINES["pup"])
        elif fed < 0.5 and rng.random() < ss["short"]:
            seals -= 1
            events.append(LINES["seals_short"])
        elif weather == "calm" and r > 0.5 and rng.random() < 0.2:
            events.append(LINES["haul_out"])
    state["seals"] = seals

    # -- puffins on the skerries ---------------------------------------
    pf = state["puffins"]
    if pf and SKERRIES and sn not in ps["away"]:   # at sea for the winter
        fed = puffin_fish / (pf * ps["need"])
        born = 0
        if fed >= ps["breed_above"] and spring and in_season(ps, sn) and pf < ps["cap"]:
            born = max(1, int(pf * ps["breed"]))
            events.append(LINES["puffins_fledged"])
        lost = rounded(pf * ps["wear"], rng)
        hungry = fed < ps["hungry_below"]
        if hungry:
            lost += rounded(pf * (ps["hungry_below"] - fed) * ps["starve"] * starve, rng)
            if not flags["puffins_hungry"]:
                events.append(LINES["puffins_hungry"])
        flags["puffins_hungry"] = hungry
        pf = max(1, pf - lost + born)
    state["puffins"] = pf

    # -- the hills: browse grows, deer graze it, wolves hunt the deer ---
    bs, ds, ws = SPECIES["browse"], SPECIES["deer"], SPECIES["wolves"]
    rs, qs, fs, cs = (SPECIES["rabbits"], SPECIES["squirrels"],
                      SPECIES["foxes"], SPECIES["cats"])
    gts, dfs = SPECIES["goats"], SPECIES["dragonflies"]
    browse, deer, wolves = state["browse"], state["deer"], state["wolves"]
    rabbits, squirrels = state["rabbits"], state["squirrels"]
    foxes, cats, goats = state["foxes"], state["cats"], state["goats"]
    deer_hungry: list[str] = []
    windfalls: list[str] = []
    dragonflies_out: list[str] = []
    berries_out: list[str] = []
    in_berries_out: list[str] = []
    birds_hungry: list[str] = []
    blossom_out: list[str] = []
    bees_out: list[str] = []
    fruit_out: list[str] = []
    poor_out: list[str] = []
    fry_out: list[str] = []
    for place in SHORES:
        name = PLACES[place]["name"]
        b, d, w = browse[place], deer[place], wolves[place]
        b += int(bs["rate"] * grow * b * (1 - b / bs["capacity"]))
        graze = min(max(0, b - bs["roots"]), d * ds["need"])
        b -= int(graze)
        # the Keep's stock grazes the same hill while it has grazing, and
        # is stabled on hay when it is bare — a steward does not turn
        # ponies onto a stripped hill
        kept_fed: dict[str, float] = {}
        for key, _ in KEPT:
            n, spec = state[key][place], SPECIES[key]
            if n:
                got = min(max(0, b - bs["roots"]), n * spec["need"]) if b > bs["bare_below"] else 0
                b -= int(got)
                kept_fed[key] = max(spec["hay"], got / (n * spec["need"]))
        r = rabbits[place]
        nibble = min(max(0, b - bs["roots"]), r * rs["need"])
        b -= int(nibble)
        gt = goats[place]
        cropped = min(max(0, b - bs["roots"]), gt * gts["need"])
        b -= int(cropped)
        bare = b < bs["bare_below"]
        # nothing fawns, kids or kindles on a bare hill: births scale with
        # how much stands above the roots, up to the bare line
        lush = min(1.0, max(0.0, (b - bs["roots"]) / (bs["bare_below"] - bs["roots"])))
        if bare and not flags["bare"][place]:
            events.append(LINES["bare"].format(place=name))
        elif flags["bare"][place] and not bare:
            events.append(LINES["greened"].format(place=name))
        flags["bare"][place] = bare
        browse[place] = b

        fed = graze / (d * ds["need"]) if d else 1.0
        # hunting falls away fast as the deer thin — a few deer on a big
        # hill are hard to find, which is what lets a herd come back
        ease = min(1.0, d / ws["easy_above"]) ** 2
        ease_g = min(1.0, gt / gts["cap"]) ** 2
        hunting = w * ws["hunt"] * (ease + 0.3 * ease_g) * (1.5 - 0.5 * work)
        kills = min(d, rounded(w * ws["hunt"] * ease * (1.5 - 0.5 * work), rng))
        kills_g = min(gt, rounded(w * ws["hunt"] * 0.3 * ease_g, rng))
        state["carrion"][place] = kills + kills_g * CARRION["goat"]
        hunted = 0
        if place == QUAY and weather == "calm" and d > ds["hunt_above"]:
            hunted = min(d - ds["hunt_above"], rounded(d * ds["hunted"], rng))
            if hunted and rng.random() < ds["table_told"]:
                events.append(LINES["table"])
        born = (rounded(d * ds["breed"] * fed * lush * (1 - d / ds["cap"]), rng)
                if d and in_season(ds, sn) else 0)
        lost = rounded(d * ds["wear"], rng) + kills + hunted
        hungry = bool(d) and fed < ds["hungry_below"]
        if hungry and d > ds["remnant"]:   # a few deer on a big hill always find enough
            lost += rounded(d * (ds["hungry_below"] - fed) * ds["starve"] * starve, rng)
            if not flags["deer_hungry"][place]:
                deer_hungry.append(place)
        flags["deer_hungry"][place] = hungry
        deer[place] = max(ds["remnant"] if d else 0, d - lost + born)

        if w:
            # judged on the hunting, not on one tide's luck: a pack goes
            # short when the deer are few, not when a night goes badly
            fed_w = hunting / (w * ws["need"])
            if (fed_w >= 1.0 and in_season(ws, sn) and w < ws["cap"]
                    and rng.random() < ws["breed"]):
                w += 1
                events.append(LINES["cub"].format(place=name))
            elif fed_w < 0.5 and rng.random() < ws["short"]:
                w -= 1
                events.append(LINES["last_wolf" if w == 0 else "wolves_short"]
                              .format(place=name))
        wolves[place] = w

        # -- the small beasts: rabbits, squirrels, foxes, the cats -------
        q, f, c = squirrels[place], foxes[place], cats[place]
        ease_r = min(1.0, r / fs["easy_above"]) ** 2
        ease_q = min(1.0, q / qs["cap"])
        fox_hunting = f * (fs["hunt"] * ease_r + fs["hunt_squirrels"] * ease_q)
        fox_hunting += min(carrion * CARRION["foxes"], f * fs["need"]) if f else 0
        sb, sbs = state["small birds"][place], SPECIES["small birds"]
        ease_b = min(1.0, sb / SPECIES["sparrowhawks"]["easy_above"]) ** 2
        cat_hunting = c * (cs["hunt"] * ease_r + cs["hunt_squirrels"] * ease_q
                           + cs["hunt_birds"] * ease_b)
        hs_, ks_ = SPECIES["harriers"], SPECIES["sparrowhawks"]
        taken_r = min(r, rounded((f * fs["hunt"] + c * cs["hunt"]
                                  + state["harriers"][place] * hs_["hunt"]) * ease_r, rng))
        taken_q = min(q, rounded((f * fs["hunt_squirrels"] + c * cs["hunt_squirrels"])
                                 * ease_q, rng))
        taken_b = min(sb, rounded((c * cs["hunt_birds"]
                                   + state["sparrowhawks"][place] * ks_["hunt"])
                                  * ease_b, rng))

        fed_r = nibble / (r * rs["need"]) if r else 1.0
        born_r = (rounded(r * rs["breed"] * fed_r * lush * (1 - r / rs["cap"]), rng)
                  if r and in_season(rs, sn) else 0)
        lost_r = rounded(r * rs["wear"], rng) + taken_r
        if r > rs["remnant"] and fed_r < rs["hungry_below"]:
            lost_r += rounded(r * (rs["hungry_below"] - fed_r) * rs["starve"] * starve, rng)
        r = max(rs["remnant"] if r else 0, r - lost_r + born_r)
        many, thin_r = r > rs["many_above"], r < rs["thin_below"]
        if many and not flags["rabbits_many"][place]:
            events.append(LINES["rabbits_many"].format(place=name))
        if thin_r and not flags["rabbits_thin"][place]:
            events.append(LINES["rabbits_thin"].format(place=name))
        flags["rabbits_many"][place], flags["rabbits_thin"][place] = many, thin_r
        rabbits[place] = r

        mast = 2.0 if sn == qs["mast"] else 1.0
        if state["fruit"][place] > 200:
            mast *= 1.5
        q += rounded(qs["rate"] * grow * mast * q * (1 - q / qs["cap"]), rng)
        if weather == "storm" and q:
            q += rounded(q * qs["windfall"], rng)
            windfalls.append(place)
        q = max(0, q - rounded(q * qs["wear"], rng) - taken_q)
        squirrels[place] = q

        # -- the worms, the berries, and the small birds on both ---------
        wms, brs = SPECIES["worms"], SPECIES["berries"]
        wm = state["worms"][place]
        wm += int(wms["rate"] * grow * wm * (1 - wm / wms["capacity"]))
        br = state["berries"][place]
        if sn in brs["ripen"]:
            br = min(brs["capacity"], br + brs["set"])
            if not flags["berries_told"][place]:
                berries_out.append(place)
            flags["berries_told"][place] = True
        elif sn not in brs["keeps"]:
            br = 0
            flags["berries_told"][place] = False
            flags["in_berries_told"][place] = False
        else:
            br -= rounded(br * brs["fade"], rng)
        if sb:
            want = sb * sbs["need"]
            from_berries = min(br, want)
            br -= int(from_berries)
            from_worms = min(wm * wms["up"][weather], want - from_berries)
            wm -= int(from_worms)
            fed_b = (from_berries + from_worms) / want
            if from_berries and not flags["in_berries_told"][place]:
                in_berries_out.append(place)
                flags["in_berries_told"][place] = True
            born_b = (rounded(sb * sbs["breed"] * fed_b * (1 - sb / sbs["cap"]), rng)
                      if in_season(sbs, sn) else 0)
            lost_b = rounded(sb * sbs["wear"], rng) + taken_b
            hungry_b = fed_b < sbs["hungry_below"]
            if hungry_b:
                lost_b += rounded(sb * (sbs["hungry_below"] - fed_b) * sbs["starve"] * starve, rng)
                if not flags["birds_hungry"][place]:
                    birds_hungry.append(place)
            flags["birds_hungry"][place] = hungry_b
            sb = max(0, sb - lost_b + born_b)
        state["small birds"][place] = sb
        state["worms"][place] = max(0, wm)
        state["berries"][place] = max(0, br)

        # -- the blossom, the bees, and the fruit they set ---------------
        fls, bes, frs = SPECIES["flowers"], SPECIES["bees"], SPECIES["fruit"]
        F, B, fr = state["flowers"][place], state["bees"][place], state["fruit"][place]
        poll = state["pollination"][place]
        if sn in fls["seasons"]:
            F = min(fls["capacity"], F + int(fls["set"] * grow))
            if not flags["blossom_told"][place]:
                blossom_out.append(place)
                flags["blossom_told"][place] = True
            poll[0] += min(1.0, B / bes["full_at"])
            poll[1] += 1
        else:
            F -= rounded(F * fls["fade"], rng)
            flags["blossom_told"][place] = False
        if B and sn not in bes["away"]:
            fed_bee = min(1.0, F / (B * bes["need"])) if F else 0.0
            if sn in fls["seasons"]:
                if fed_bee > 0.5 and not flags["bees_told"][place]:
                    bees_out.append(place)
                    flags["bees_told"][place] = True
                if (fed_bee >= 0.8 and in_season(bes, sn) and B < bes["cap"]
                        and rng.random() < bes["breed"]):
                    B += 1
            if weather == "storm":
                B -= rounded(B * bes["storm_loss"], rng)
            B = max(1, B)
        if sn == "winter":
            flags["bees_told"][place] = False
        if sn in frs["ripen"]:
            index = (poll[0] / poll[1]) if poll[1] else 0.0
            if not flags["fruit_told"][place]:
                (poor_out if index < frs["poor_below"] else fruit_out).append(place)
                flags["fruit_told"][place] = True
            fr = min(frs["capacity"], fr + int(frs["set"] * index))
        else:
            if flags["fruit_told"][place] and sn == "winter":
                flags["fruit_told"][place] = False
                poll[0], poll[1] = 0.0, 0
            fr -= rounded(fr * 0.1, rng)
        eaten = min(fr, int(d * 0.2 + q * 0.03 + sb * 0.01))
        fr -= eaten
        if place == QUAY:
            picked_fruit = min(fr // 10, 20)
        elif place == HERMITS["island"]:
            picked_fruit = min(fr // 10, 8)
        else:
            picked_fruit = 0
        fr -= picked_fruit
        state["gathered_fruit"] += picked_fruit
        state["flowers"][place] = max(0, F)
        state["bees"][place] = B
        state["fruit"][place] = max(0, fr)

        # -- fishing eagles ----------------------------------------------
        E = state["fishing eagles"][place]
        if E:
            fed_e = work if state["herring"] > 0 else 0.0
            if (fed_e >= 0.8 and spring and in_season(es, sn) and E < es["cap"]
                    and rng.random() < es["breed"]):
                E += 1
                events.append(LINES["eaglets"].format(place=name))
            elif fed_e < 0.3 and E > 1 and rng.random() < es["short"]:
                E -= 1
            elif weather in ("calm", "fresh") and rng.random() < 0.008:
                events.append(LINES["eagle"])
        state["fishing eagles"][place] = E

        # -- the coves and the caves -------------------------------------
        if PLACES[place].get("coves"):
            if sn in ("spring", "summer") and spring and weather == "calm":
                if not flags["fry_told"][place]:
                    fry_out.append(place)
                    flags["fry_told"][place] = True
            elif sn == "winter":
                flags["fry_told"][place] = False
        if (PLACES[place].get("caves") and weather == "storm" and sn == "winter"
                and rng.random() < 0.1):
            events.append(LINES["caves"])

        if f:
            fed_f = (fox_hunting + (scraps * 0.1 if place == QUAY else 0)) / (f * fs["need"])
            if (fed_f >= 1.0 and in_season(fs, sn) and f < fs["cap"]
                    and rng.random() < fs["breed"]):
                f += 1
                events.append(LINES["fox_cubs"].format(place=name))
            elif fed_f < 0.5 and f > fs["remnant"] and rng.random() < fs["short"]:
                f -= 1
                events.append(LINES["foxes_short"].format(place=name))
        foxes[place] = f

        if c:
            fed_c = cat_hunting / (c * cs["need"])
            if (fed_c >= 1.0 and in_season(cs, sn) and c < cs["cap"]
                    and rng.random() < cs["breed"]):
                c += 1
                events.append(LINES["kittens"])
            elif c > cs["kept"]:
                # the kitchens keep a floor under the cats; above it they
                # live or die by the hunting like anything else
                c -= rounded(c * cs["wear"], rng)
                if fed_c < 0.5 and rng.random() < cs["short"]:
                    c -= 1
                    events.append(LINES["cats_short"])
            c = max(c, cs["kept"])
        cats[place] = c

        # -- goats on the crags ------------------------------------------
        if gt:
            fed_g = max(gts["crags"], cropped / (gt * gts["need"]))
            born_g = (rounded(gt * gts["breed"] * fed_g * lush * (1 - gt / gts["cap"]), rng)
                      if in_season(gts, sn) else 0)
            if born_g and spring:
                events.append(LINES["kid"].format(place=name))
            lost_g = rounded(gt * gts["wear"], rng) + kills_g
            hungry_g = fed_g < gts["hungry_below"]
            if hungry_g and gt > gts["remnant"]:
                lost_g += rounded(gt * (gts["hungry_below"] - fed_g) * gts["starve"] * starve, rng)
                if not flags["goats_hungry"][place]:
                    events.append(LINES["goats_hungry"].format(place=name))
            flags["goats_hungry"][place] = hungry_g
            gt = max(gts["remnant"], gt - lost_g + born_g)
            if (place == HERMITS["island"] and gt > gts["remnant"]
                    and rng.random() < HERMITS["goat"]):
                gt -= 1
                events.append(LINES["hermits_goat"])
        goats[place] = gt
        if place == HERMITS["island"]:
            if weather == "calm" and rng.random() < HERMITS["smoke"]:
                events.append(LINES["smoke"])
            if weather == "storm" and rng.random() < HERMITS["stranded"]:
                events.append(LINES["stranded"])
            elif weather == "calm" and rng.random() < HERMITS["arrived"]:
                events.append(LINES["arrived"])

        # -- dragonflies over the pools -----------------------------------
        df = state["dragonflies"][place]
        if weather == "calm" and in_season(dfs, sn):
            df += rounded(dfs["hatch"] * df * (1 - df / dfs["cap"]), rng)
        df -= rounded(df * dfs["blown"][weather], rng)
        df = max(dfs["seed"], df)
        many_df = df > dfs["many_above"]
        if many_df and not flags["dragonflies"][place]:
            dragonflies_out.append(place)
        flags["dragonflies"][place] = many_df
        state["dragonflies"][place] = df

        # -- the hunters of small things ----------------------------------
        for key, fledged_line, short_line in HUNTERS:
            n, spec = state[key][place], SPECIES[key]
            if not n:
                continue
            prey = state[spec["prey"]][place]
            ease_p = min(1.0, prey / spec["easy_above"]) ** 2
            fed_h = (spec["hunt"] * ease_p + spec["base"]) / spec["need"]
            if (fed_h >= 1.0 and spring and in_season(spec, sn) and n < spec["cap"]
                    and rng.random() < spec["breed"]):
                n += 1
                events.append(LINES[fledged_line].format(place=name))
            elif fed_h < 0.5 and n > spec["remnant"] and rng.random() < spec["short"]:
                n -= 1
                events.append(LINES[short_line].format(place=name))
            state[key][place] = n

        # -- the Keep's stock ---------------------------------------------
        for key, line in KEPT:
            n, spec = state[key][place], SPECIES[key]
            if not n:
                continue
            fed_k = kept_fed.get(key, spec["hay"])
            if (fed_k >= 1.0 and in_season(spec, sn) and n < spec["cap"]
                    and rng.random() < spec["breed"]):
                n += 1
                events.append(LINES[line])
            elif n > spec["kept"]:
                n -= rounded(n * spec["wear"], rng)
            state[key][place] = max(n, spec["kept"])
    for places, one, every in ((deer_hungry, "deer_hungry", "deer_hungry_all"),
                               (windfalls, "windfall", "windfall_all"),
                               (dragonflies_out, "dragonflies", "dragonflies_all"),
                               (berries_out, "berries", "berries_all"),
                               (in_berries_out, "in_berries", "in_berries_all"),
                               (birds_hungry, "birds_hungry", "birds_hungry_all"),
                               (blossom_out, "blossom", "blossom_all"),
                               (bees_out, "bees", "bees_all"),
                               (fruit_out, "fruit", "fruit_all"),
                               (poor_out, "poor_fruit", "poor_fruit_all"),
                               (fry_out, "cove_fry", "cove_fry_all")):
        if len(places) == len(SHORES) > 1:
            events.append(LINES[every])
        else:
            events.extend(LINES[one].format(place=PLACES[k]["name"]) for k in places)
    if label == "neap" and weather == "calm":
        for key, line in CROSSERS:
            pack, spec = state[key], SPECIES[key]
            for place in SHORES:
                if pack[place]:
                    continue
                for other in PLACES[place].get("narrows", []):
                    if pack.get(other, 0) >= spec["cross_from"]:
                        pack[other] -= spec["crossing"]
                        pack[place] = spec["crossing"]
                        events.append(LINES[line].format(place=PLACES[place]["name"]))
                        break

    # -- the Warden writes what the Guild will not say aloud ----------
    if FERRY:
        rings = 1 + (1 if r > 0.5 else 0) + (
            1 if work >= 0.8 and rng.random() < 0.6 else 0)
        state["warden"].append([t, rings, aboard, catch])

    # -- the line ----------------------------------------------------
    clauses = list(events)
    if FERRY:
        if weather == "storm" and aboard == 0:
            clauses.append(LINES["ferry_storm"])
        elif aboard == 0:
            clauses.append(LINES["ferry_empty"])
        else:
            ferry = LINES["ferry"].format(aboard=words(aboard))
            if in_news:
                ferry += ", " + LINES["in_news"].format(n=words(in_news))
            clauses.append(ferry)
    if not events:
        pool = LINES.get("quiet_pool")
        clauses.append(rng.choice(pool) if pool else LINES["quiet"])
    line = LINES["tide"].format(tide=t + 1, season=sn, label=label, weather=weather,
                                clauses="; ".join(clauses))
    state["chronicle"].append(line)
    state["tide"] = t + 1
    return line


def sea_events(state, rng, sn, season, r, weather, spring, stir, events) -> None:
    """One tide of the open sea and the reef: the plankton, the shoals, the
    dolphins and whales, the coral and its fish. Seen from a deck."""
    flags = state["flags"]
    # the plankton, the sea's own bloom
    level = BLOOM_LEVEL * season["bloom"]
    P = clamp(state["plankton"] + int((level - state["plankton"]) * 0.1) + stir, 0, 100)
    state["plankton"] = P
    # the shoals
    ss, S = SPECIES["shoals"], state["shoals"]
    S += int(ss["rate"] * (P / 100) * (1 + state["rafts"] / 100) * S * (1 - S / ss["capacity"]))
    ds, D = SPECIES["dolphins"], state["dolphins"]
    ease = min(1.0, S / ds["easy_above"]) ** 2
    taken = min(S, rounded(D * ds["fish_each"] * ease, rng))
    S -= taken
    if flags["shoals_thin"] and sn == "spring" and spring and S < ss["thin_below"]:
        S += ss["run"]
        events.append(LINES["shoals_run"])
    thin = S < ss["thin_below"]
    if thin and not flags["shoals_thin"]:
        events.append(LINES["shoals_thin"])
    flags["shoals_thin"] = thin
    if not thin and weather in ("calm", "fresh") and rng.random() < 0.03:
        events.append(LINES["shoal_silver"])
    state["shoals"] = S
    # the dolphins
    if D:
        fed = taken / (D * ds["need"])
        if fed >= 1.0 and in_season(ds, sn) and D < ds["cap"] and rng.random() < ds["breed"]:
            D += 1
            events.append(LINES["dolphins_born"])
        elif fed < 0.5 and D > 2 and rng.random() < ds["short"]:
            D -= 1
            events.append(LINES["dolphins_short"])
        elif weather in ("calm", "fresh") and rng.random() < 0.06:
            events.append(LINES["dolphins"])
    state["dolphins"] = D
    # the whales, here for the warm half of the year
    ws, W = SPECIES["whales"], state["whales"]
    home = sn not in ws["away"]
    if home and not flags["whales_home"]:
        events.append(LINES["whales_back"])
    elif flags["whales_home"] and not home:
        events.append(LINES["whales_gone"])
    flags["whales_home"] = home
    if W and home:
        fed = P / ws["need"]
        if fed >= 1.0 and in_season(ws, sn) and W < ws["cap"] and rng.random() < ws["breed"]:
            W += 1
            events.append(LINES["calf"])
        elif fed < 0.5 and W > 2 and rng.random() < ws["short"]:
            W -= 1
            events.append(LINES["whales_short"])
        elif weather in ("calm", "fresh") and rng.random() < 0.05:
            events.append(LINES["whales_blow"])
    state["whales"] = W
    # the coral, and the fish on it
    cs, C = SPECIES["coral"], state["coral"]
    if sn in cs["warm"] and weather in ("calm", "fresh"):
        C += int(cs["rate"] * C * (1 - C / cs["capacity"]))
    if weather == "storm":
        broke = rounded(C * cs["storm_break"], rng)
        C -= broke
        if broke >= cs["broke_told"]:
            events.append(LINES["reef_broke"])
    elif spring and weather == "calm" and rng.random() < 0.15:
        events.append(LINES["reef_showing"])
    state["coral"] = max(0, C)
    rs, R = SPECIES["reef fish"], state["reef fish"]
    cap = max(1, int(C * rs["per_coral"]))
    if R:
        R += rounded(rs["rate"] * season["bloom"] * R * (1 - R / cap), rng) if in_season(rs, sn) else 0
        R -= rounded(R * rs["wear"], rng)
        if R > cap:
            R -= (R - cap) // 4
        if R > 0.8 * cap and weather == "calm" and rng.random() < 0.03:
            events.append(LINES["reef_fish"])
    state["reef fish"] = max(1, R) if R or C else 0
    # the rafts of sea trees, and the sea ostriches that ride them
    rf, K = SPECIES["rafts"], state["rafts"]
    if sn in rf["seasons"] and weather == "calm" and K < rf["cap"] and rng.random() < rf["form"]:
        K += 1
    if weather == "storm":
        lost = rounded(K * rf["break"], rng)
        K -= lost
        if lost >= rf["broke_told"]:
            events.append(LINES["rafts_broke"])
    elif sn == "winter":
        K -= rounded(K * rf["sink"], rng)
    elif K and weather in ("calm", "fresh") and rng.random() < 0.03:
        events.append(LINES["raft"])
    K = max(0, K)
    state["rafts"] = K
    os_, O = SPECIES["sea ostriches"], state["sea ostriches"]
    if O:
        nests = K * os_["per_raft"]
        fed = min(1.0, S / ds["easy_above"])
        if (fed >= 0.5 and in_season(os_, sn) and O < min(os_["cap"], nests)
                and rng.random() < os_["breed"]):
            O += 1
            events.append(LINES["ostrich_chicks"])
        if weather == "storm":
            O -= rounded(O * os_["storm_loss"], rng)
        if O > nests and sn == "winter" and rng.random() < 0.1:
            O -= 1
        if fed < 0.5 and rng.random() < 0.02:
            O -= 1
            events.append(LINES["ostriches_short"])
        elif K and weather in ("calm", "fresh") and rng.random() < 0.04:
            events.append(LINES["ostriches"])
    state["sea ostriches"] = max(0, O)


def run(state: dict, tides: int, out=None) -> None:
    for _ in range(tides):
        line = step(state)
        if out:
            print(line, file=out)


def summary(state: dict) -> list[str]:
    ed = EDITIONS[EDITION]
    lines = [f"After {state['tide']} tides (seed {state['seed']}):"]
    for key in ed["places"]:
        place = PLACES[key]
        name = place["name"]
        if key in ed["unsimulated"]:
            lines.append(f"  {name:<40} {LINES['own_account']}")
        elif key == "sounds":
            lines.append(f"  {name:<40} herring {state['herring']}   "
                         f"bloom {state['bloom']}")
        elif place.get("shore"):
            lines.append(f"  {name:<40} gulls {state['gulls'][key]}   "
                         f"shellfish {state['shellfish'][key]}")
            lines.append(f"  {'':<40} grazing {state['browse'][key]}   "
                         f"deer {state['deer'][key]}   "
                         f"wolves {state['wolves'][key]}   "
                         f"rabbits {state['rabbits'][key]}   "
                         f"foxes {state['foxes'][key]}   "
                         f"squirrels {state['squirrels'][key]}   "
                         f"cats {state['cats'][key]}")
            lines.append(f"  {'':<40} goats {state['goats'][key]}   "
                         f"harriers {state['harriers'][key]}   "
                         f"sparrowhawks {state['sparrowhawks'][key]}   "
                         f"dragonflies {state['dragonflies'][key]}   "
                         f"ponies {state['ponies'][key]}   "
                         f"alpacas {state['alpacas'][key]}")
            lines.append(f"  {'':<40} small birds {state['small birds'][key]}   "
                         f"worms {state['worms'][key]}   "
                         f"berries {state['berries'][key]}")
            lines.append(f"  {'':<40} blossom {state['flowers'][key]}   "
                         f"bees {state['bees'][key]}   fruit {state['fruit'][key]}   "
                         f"fishing eagles {state['fishing eagles'][key]}")
        elif key == "skerries":
            lines.append(f"  {name:<40} seals {state['seals']}   "
                         f"puffins {state['puffins']}")
        elif key == "sea":
            whales = state["whales"] if state["flags"]["whales_home"] else "away"
            lines.append(f"  {name:<40} plankton {state['plankton']}   "
                         f"shoals {state['shoals']}   dolphins {state['dolphins']}   "
                         f"whales {whales}")
            lines.append(f"  {'':<40} rafts of sea trees {state['rafts']}   "
                         f"sea ostriches {state['sea ostriches']}")
        elif key == "reef":
            lines.append(f"  {name:<40} coral {state['coral']}   "
                         f"reef fish {state['reef fish']}")
    if SHORES:
        lines.append(f"  {LINES['off_record']:<40} gulls {state['south']}")
    if FERRY:
        g = state["guild"]
        lines.append(f"  The Guild's ledger: {g['crossings']} crossings, "
                     f"{g['coin']} fares in coin, {g['news']} in news, "
                     f"{g['empty']} crossed empty and owed for.")
    if QUAY:
        lines.append(f"  Landed at {PLACES[QUAY]['name']}'s quay: "
                     f"{state['landed']} herring.")
    if state["gathered"]:
        lines.append("  " + LINES["gathered"].format(n=state["gathered"]))
    if state["gathered_fruit"]:
        lines.append(f"  Fruit gathered: {state['gathered_fruit']}.")
    if FERRY:
        lines.append(f"  The Warden's ledger runs to {len(state['warden'])} lines; "
                     "--ledger shows it.")
    return lines


def roles(state: dict) -> list[tuple[str, str, list[str]]]:
    """Who does what, for the places this edition holds: each role with
    the plants and species present under it."""
    ed = EDITIONS[EDITION]
    out = []
    for role, gloss in ROLES:
        names = []
        if role == "grows":
            for plant, where in PLANTS.items():
                if where in ed["places"] or (where == "shore" and SHORES):
                    names.append(plant)
        for key, spec in SPECIES.items():
            if spec.get("role") != role:
                continue
            if spec.get("lives") and spec["lives"] not in ed["places"]:
                continue
            count = state.get(key, 0)
            present = sum(count.values()) if isinstance(count, dict) else count
            if present:
                names.append(key)
        if names:
            out.append((role, gloss, names))
    return out


def ledger(state: dict) -> list[str]:
    lines = ["The Warden's ledger — what the Crown counts and the Guild "
             "will not say aloud.",
             f"  {'tide':>5}  {'rings':>5}  {'aboard':>6}  {'landed':>6}"]
    for tide, rings, aboard, landed in state["warden"]:
        lines.append(f"  {tide + 1:>5}  {rings:>5}  {aboard:>6}  {landed:>6}")
    return lines


def render_html(state: dict, companies_lines: list[str], date: str) -> str:
    """The chronicle and summary as one self-contained page, in the quest's
    own palette. No ledger: the rings stay with the Warden."""
    esc = html.escape
    head = "\n".join(f"<p class=\"company\">{esc(c)}</p>" for c in companies_lines)
    lines = "\n".join(f"<li>{esc(line)}</li>" for line in state["chronicle"])
    after = "\n".join(f"<li>{esc(line.strip())}</li>" for line in summary(state)[1:]
                       if "--ledger" not in line)
    also = "".join(f' · <a href="{esc(href)}">{esc(text)}</a>'
                   for text, href in PAGE.get("links", []))
    who = "\n".join(
        f"<li><b>{esc(role)}</b> — {esc(gloss)}: {esc(', '.join(names))}</li>"
        for role, gloss, names in roles(state))
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(PAGE["title"])} · {esc(PAGE["kicker"])}</title>
<style>
  :root {{ --ground:#f6f2e8; --panel:#ffffff; --ink:#2b2620; --dim:#6f675a;
           --sea:#1d5f6e; --gold:#8a6d1f; --line:#d9d2c2; }}
  * {{ box-sizing: border-box; }}
  body {{ margin:0; background:var(--ground); color:var(--ink);
          font:17px/1.65 Georgia, "Times New Roman", serif; }}
  header {{ padding:1.2rem 1.5rem .9rem; border-bottom:1px solid var(--line);
            background:var(--panel); }}
  header h1 {{ margin:0 0 .2rem; font-size:1.5rem; letter-spacing:.02em; }}
  header p {{ margin:0; color:var(--dim); font-style:italic; }}
  main {{ max-width:44rem; margin:0 auto; padding:1.2rem 1.5rem 4rem; }}
  h2 {{ font-size:.8rem; letter-spacing:.14em; text-transform:uppercase;
        color:var(--sea); margin:1.6rem 0 .5rem; }}
  ul {{ padding-left:1.1rem; }}
  li {{ margin:.35rem 0; }}
  .company {{ color:var(--dim); margin:.3rem 0; }}
  .after li {{ color:var(--dim); }}
  a {{ color:var(--sea); }}
  footer {{ color:var(--dim); font-size:.92em; margin-top:2rem;
            border-top:1px solid var(--line); padding-top:.8rem; }}
</style>
</head>
<body>
<header>
  <h1>{esc(PAGE["title"])}</h1>
  <p>{esc(PAGE["kicker"])} · <a href="../">{esc(PAGE["back"])}</a>{also}</p>
</header>
<main>
<p>{esc(PAGE["lede"].format(date=date))}</p>
{head}
<h2>{esc(PAGE["chronicle"])}</h2>
<ul>
{lines}
</ul>
<h2>{esc(PAGE["after"])}</h2>
<ul class="after">
{after}
</ul>
<h2>{esc(PAGE["roles"])}</h2>
<ul class="after">
{who}
</ul>
<footer>{esc(PAGE["foot"])}</footer>
</main>
</body>
</html>
"""


def companies(root: str) -> list[str]:
    """Name the companies on the water, read from index.html. Absent
    file or absent company: nothing is said, and nothing is invented."""
    try:
        here = os.path.dirname(os.path.abspath(__file__))
        sys.path.insert(0, os.path.join(here, "..", "teller"))
        import questfile  # noqa: E402
        path = questfile.find_quest(root)
        if not path:
            return []
        factions = questfile.load_quest(path)["factions"]
    except Exception:
        return []
    out = []
    for key in COMPANIES_ON_THE_WATER:
        f = factions.get(key)
        if f and f.get("name") and f.get("quest"):
            out.append(LINES["companies"].format(name=f["name"],
                                                 quest=f["quest"]))
    return out


def load_state(path: str) -> dict | None:
    try:
        with open(path, encoding="utf-8") as fh:
            s = json.load(fh)
        if isinstance(s, dict) and isinstance(s.get("tide"), int):
            configure(s.get("edition", "sounds"))
            return s
    except (OSError, ValueError):
        pass
    return None


def save_state(path: str, state: dict) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(state, fh, indent=1)
        fh.write("\n")


# -- the invariants ---------------------------------------------------

COUNTED = ("gulls", "shellfish", "deer", "wolves", "browse", "rabbits",
           "squirrels", "foxes", "cats", "goats", "dragonflies", "harriers",
           "sparrowhawks", "ponies", "alpacas", "small birds", "worms", "berries",
           "flowers", "bees", "fruit", "fishing eagles")


def check() -> list[str]:
    """What is always true of the sandbox, or the sandbox is wrong."""
    problems: list[str] = []

    def bad(msg: str) -> None:
        problems.append(msg)

    for seed in range(1, 8):
        s = fresh_state(seed)
        run(s, 3 * TIDES_PER_CYCLE)
        if min(s["herring"], s["seals"], s["puffins"], s["south"]) < 0:
            bad(f"seed {seed}: a count went negative")
        for place in SHORES:
            for key in COUNTED:
                if s[key][place] < 0:
                    bad(f"seed {seed}: {key} on {place} went negative")
        for key in COUNTED:
            if "fourth" in s[key]:
                bad(f"seed {seed}: Fourth Island acquired {key}")
        if s["guild"]["crossings"] != s["tide"]:
            bad(f"seed {seed}: the ferry missed a tide")
        if len(s["warden"]) != s["tide"]:
            bad(f"seed {seed}: the Warden missed a tide")
        for line in s["chronicle"]:
            if re.search(r"\brings?\b", line):
                bad(f"seed {seed}: the chronicle counted the bell aloud: {line}")
            if "ferry crossed" not in line:
                bad(f"seed {seed}: a tide without a crossing: {line}")
            if not any(f" · {x['name']} · " in line for x in SEASONS):
                bad(f"seed {seed}: a tide without a season: {line}")
            if PLACES["fourth"]["name"] in line:
                bad(f"seed {seed}: the chronicle spoke of Fourth Island: {line}")

    # the open sea: no ferry, no ledger, whales that come and go
    for seed in range(1, 5):
        s = fresh_state(seed, "sea")
        run(s, YEAR_TIDES + 200)
        for key in ("shoals", "dolphins", "whales", "coral", "reef fish", "plankton",
                    "rafts", "sea ostriches"):
            if s[key] < 0:
                bad(f"sea, seed {seed}: {key} went negative")
        text = "\n".join(s["chronicle"] + summary(s))
        for word in ("ferry", "fare", "Guild", "Warden", "ledger", "quay", "gulls fledged"):
            if word in text:
                bad(f"sea, seed {seed}: the account spoke of the {word}")
        if LINES["whales_back"] not in text or LINES["whales_gone"] not in text:
            bad(f"sea, seed {seed}: the whales neither came nor went in a year")
    a, b = fresh_state(2, "sea"), fresh_state(2, "sea")
    run(a, 40)
    run(b, 40)
    if a != b:
        bad("sea: two runs of one seed differed")
    page = render_html(a, [], "a day")
    if PAGE["title"] not in page or "dolphins" not in page:
        bad("sea: the page does not carry the account")

    # Fourth Island: its own account — no ferry, no ledger, no counted hermit
    for seed in range(1, 6):
        s = fresh_state(seed, "fourth")
        run(s, 3 * TIDES_PER_CYCLE)
        if min(s["herring"], s["south"], s["gathered"]) < 0:
            bad(f"fourth, seed {seed}: a count went negative")
        for key in COUNTED:
            if s[key]["fourth"] < 0:
                bad(f"fourth, seed {seed}: {key} went negative")
            if len(s[key]) != 1:
                bad(f"fourth, seed {seed}: {key} counted on more than the island")
        if s["warden"] or s["guild"]["crossings"]:
            bad(f"fourth, seed {seed}: a ferry crossed, or the Warden wrote")
        text = "\n".join(s["chronicle"] + summary(s))
        for word in ("ferry", "fare", "Guild", "Warden", "ledger", "quay"):
            if word in text:
                bad(f"fourth, seed {seed}: the account spoke of the {word}")
        if re.search(r"\brings?\b", text) or re.search(r"\d+ (hermits?|sailors?)", text):
            bad(f"fourth, seed {seed}: the bell was counted, or the hermits were")
    a, b = fresh_state(4, "fourth"), fresh_state(4, "fourth")
    run(a, 40)
    run(b, 40)
    if a != b:
        bad("fourth: two runs of one seed differed")
    page = render_html(a, [], "a day")
    if PAGE["title"] not in page or a["chronicle"][-1].split(" — ")[0] not in page:
        bad("fourth: the page does not carry the account")

    # a year turns through all four seasons, in order, from any start
    s = fresh_state(6, "sounds", year_tide=200)
    run(s, YEAR_TIDES)
    turns = [m.group(1) for line in s["chronicle"]
             for m in [re.search(r"\b(winter|spring|summer|autumn) came in\b", line)] if m]
    order = [x["name"] for x in SEASONS]
    i = order.index(season_for(200)["name"])
    if turns != order[i + 1:] + order[:i + 1]:
        bad(f"the year did not turn through its seasons in order: {turns}")
    if not roles(s) or not any(role == "grows" for role, _, _ in roles(s)):
        bad("the roles table is empty, or nothing grows")

    # the page says what the chronicle says, and nothing the Warden keeps
    s = fresh_state(2)
    run(s, TIDES_PER_CYCLE)
    page = render_html(s, ["On the water: a company — its quest"], "a day")
    if PAGE["title"] not in page or s["chronicle"][-1].split(" — ")[0] not in page:
        bad("the page does not carry the chronicle")
    if PAGE["roles"] not in page:
        bad("the page does not say who does what")
    if re.search(r"\brings?\b", page) or "--ledger" in page:
        bad("the page counted the bell aloud, or pointed at the Warden's ledger")

    # the same seed is the same world
    a, b = fresh_state(3), fresh_state(3)
    run(a, 40)
    run(b, 40)
    if a != b:
        bad("two runs of one seed differed")

    # a run continued from a saved state is the run played straight through
    straight = fresh_state(5)
    run(straight, 40)
    halves = fresh_state(5)
    run(halves, 20)
    halves = json.loads(json.dumps(halves))
    run(halves, 20)
    if straight != halves:
        bad("a run continued from a save differed from one played straight")
    if straight["chronicle"][:20] != halves["chronicle"][:20]:
        bad("continuing a run rewrote its past")

    configure("sounds")
    return problems


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--tides", type=int, default=TIDES_PER_CYCLE,
                    help=f"tides to run (default one cycle, {TIDES_PER_CYCLE})")
    ap.add_argument("--seed", type=int, default=1, help="which world (default 1)")
    ap.add_argument("--edition", choices=sorted(EDITIONS), default="sounds",
                    help="the Sounds (default), or Fourth Island's own account")
    ap.add_argument("--state", metavar="PATH",
                    help="continue from this file and save back to it")
    ap.add_argument("--history", action="store_true",
                    help="with --state: show the chronicle so far, run nothing")
    ap.add_argument("--ledger", action="store_true",
                    help="show the Warden's ledger after the run")
    ap.add_argument("--quiet", action="store_true",
                    help="summary only, no chronicle")
    ap.add_argument("--json", action="store_true",
                    help="print the final state as JSON instead of prose")
    ap.add_argument("--html", metavar="PATH",
                    help="write the chronicle and summary as a page to PATH")
    ap.add_argument("--date", default=None,
                    help="the date the run starts on and the page names "
                         "(YYYY-MM-DD; default: today, UTC, for --html only)")
    ap.add_argument("--roles", action="store_true",
                    help="show who does what after the run")
    ap.add_argument("--repo", default=os.path.join(
        os.path.dirname(os.path.abspath(__file__)), ".."),
        help="repository whose index.html names the companies")
    ap.add_argument("--check", action="store_true",
                    help="check the invariants and exit")
    args = ap.parse_args()

    if args.check:
        problems = check()
        for p in problems:
            print(f"  FAIL: {p}")
        print("sandbox: ok" if not problems else
              f"sandbox: {len(problems)} failure(s)")
        return 1 if problems else 0

    state = load_state(args.state) if args.state else None
    if state is None:
        start = None
        if args.date:
            start = datetime.date.fromisoformat(args.date)
        elif args.html:
            start = datetime.date.today()
        state = fresh_state(args.seed, args.edition,
                            year_tide_for(start) if start else 0)

    if args.history:
        if not args.state:
            print("--history needs --state: there is no past without a record")
            return 2
        for line in state["chronicle"]:
            print(line)
        return 0

    quiet = args.quiet or args.json or bool(args.html)
    company_lines = companies(os.path.abspath(args.repo)) if FERRY else []
    if not quiet:
        for line in company_lines:
            print(line)
        if state["tide"]:
            print(f"Continuing from tide {state['tide']}.")
        print()
    run(state, args.tides, out=None if quiet else sys.stdout)
    if args.state:
        save_state(args.state, state)

    if args.html:
        date = args.date or datetime.date.today().isoformat()
        os.makedirs(os.path.dirname(os.path.abspath(args.html)), exist_ok=True)
        with open(args.html, "w", encoding="utf-8") as fh:
            fh.write(render_html(state, company_lines, date))
        print(f"wrote {args.html}: {state['tide']} tides, seed {state['seed']}")
        return 0

    if args.json:
        print(json.dumps(state, indent=1))
        return 0
    print()
    for line in summary(state):
        print(line)
    if args.ledger:
        print()
        for line in ledger(state):
            print(line)
    if args.roles:
        print()
        for role, gloss, names in roles(state):
            print(f"  {role} — {gloss}: {', '.join(names)}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BrokenPipeError:      # `| head` is a fair way to read a chronicle
        raise SystemExit(0)
