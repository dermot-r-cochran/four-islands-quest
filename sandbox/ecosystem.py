#!/usr/bin/env python3
"""ecosystem — a mini sandbox of the Four Sounds, one tide at a time.

Not a chapter and not a player. A small living model of the waters the
kingdom is named for: the bloom the tide stirs up, the herring that feed on
it, the shellfish on three shores, the gulls that eat both, the seals on the
skerries; on the hills above, the browse, the fallow deer that graze it and
the wolves that hunt them — and the two companies that work the water every
tide. The Ferrymen's Guild crosses on any tide and is owed for it. The
Crown's Warden writes down what the Guild will not say aloud.

    python3 sandbox/ecosystem.py                       # one tide-cycle, seed 1
    python3 sandbox/ecosystem.py --tides 84 --seed 7   # longer, elsewhere
    python3 sandbox/ecosystem.py --state .ecosystem-state.json   # keeps going between visits
    python3 sandbox/ecosystem.py --state .ecosystem-state.json --history   # the written past
    python3 sandbox/ecosystem.py --ledger              # the Warden's ledger, rings and all
    python3 sandbox/ecosystem.py --check               # the invariants hold

Standard library only: nothing installed, fetched, or executed from
elsewhere. The companies it names are read out of `index.html` through
`teller/questfile.py`, so the sandbox stands behind the same record as the
quest rather than keeping a second copy of it.

The world data at the top is the sandbox's own and is soft content in
WORLD.md's sense — bounded by the spine, owed nothing by any chapter. The
engine below it never needs editing to re-voice or re-stock the sandbox.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import random
import re
import sys

# ============================================================
# WORLD DATA — the sandbox's own. CC BY 4.0, see CONTENT-LICENSE.md.
# Soft content: bounded by the spine in WORLD.md, contradicted freely
# by a better idea in a later chapter. Fourth Island is listed and not
# simulated: there is nothing behind it until it is written.
# ============================================================

TIDES_PER_CYCLE = 28   # two tides a day; springs a fortnight apart

PLACES = {
    "sounds":   {"name": "the Sounds"},
    "first":    {"name": "First Island", "shore": True, "quay": True},
    "second":   {"name": "Second Island", "shore": True, "narrows": ["third"]},
    "third":    {"name": "Third Island", "shore": True, "narrows": ["second"]},
    "skerries": {"name": "the skerries between Second and Third"},
    "fourth":   {"name": "Fourth Island", "unwritten": True},
}

SPECIES = {
    # The herring live in the Sounds and feed on the bloom. When the
    # Sounds run thin, a new shoal comes in from the open sea on a spring
    # tide — herring are travellers, and the kingdom is on their road.
    "herring":   {"capacity": 4000, "rate": 0.6, "start": 1800, "shoal": 600,
                  "thin_below": 500},
    # Shellfish on every written shore. They feed while the water is over
    # them, so the big tides suit them; spat settles on a bare shore at
    # the springs.
    "shellfish": {"capacity": 800, "rate": 0.15, "start": 500, "spat": 40,
                  "bare_below": 40},
    # Gulls nest on every written shore, fish the Sounds when the water
    # can be worked, turn to the shore when it cannot, and take the
    # scraps at First Island's quay. Fledging happens on the springs.
    "gulls":     {"start": {"first": 120, "second": 90, "third": 70},
                  "cap": 400, "need": 1.0, "herring_take": 0.9,
                  "shore_take": 0.6, "breed": 0.05, "wear": 0.005,
                  "hungry_below": 0.6, "starve": 0.1, "wander": 0.02},
    # Seals on the skerries, fishing the same herring.
    "seals":     {"start": 12, "cap": 40, "fish_each": 4, "short": 0.2},
    # The hills: browse on every written island, grazed by the deer. A
    # stripped hill regrows from the root, slowly.
    "browse":    {"capacity": 3000, "rate": 0.03, "start": 2000, "regrow": 40,
                  "bare_below": 200},
    # Fallow deer on every written island, fawning when the hill feeds
    # them. First Island's are the Keep's to hunt, in fair weather.
    "deer":      {"start": {"first": 24, "second": 36, "third": 30},
                  "cap": 120, "need": 0.5, "breed": 0.015, "wear": 0.005,
                  "hungry_below": 0.6, "starve": 0.2, "hunt_above": 15,
                  "hunted": 0.1},
    # Wolves, in packs, on the two islands with narrows between them. A
    # pack that dies out is replaced from across the narrows at a calm
    # neap, when the water between is narrowest.
    "wolves":    {"start": {"second": 5, "third": 4}, "cap": 10, "hunt": 0.06,
                  "need": 0.05, "easy_above": 40, "breed": 0.03, "short": 0.15,
                  "cross_from": 6, "crossing": 2},
}

WEATHER = [("calm", 35), ("fresh", 40), ("blowing", 18), ("storm", 7)]
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

# What the chronicle says. The engine fills the braces and joins the
# clauses; every word a player reads is here.
LINES = {
    "tide":        "Tide {tide} · {label} · {weather} — {clauses}.",
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
    "south":       "some gulls went south, and the record does not follow them",
    "north":       "gulls came back from the south; where they had been, "
                   "the record does not say",
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
    "catch":       "a good catch landed at {place}",
    "ferry":       "the ferry crossed with {aboard} aboard",
    "ferry_empty": "the ferry crossed empty, and is owed for it",
    "ferry_storm": "the ferry crossed anyway",
    "in_news":     "{n} paying in news",
    "numbers":     ["no", "one", "two", "three", "four", "five", "six"],
    "companies":   "On the water: {name} — {quest}",
    "not_written": "not simulated — nothing is written of it",
}

# ============================================================
# ENGINE — MIT, see LICENSE. Reads the data above; adds no words.
# ============================================================

SHORES = [k for k, p in PLACES.items() if p.get("shore")]
QUAY = next(k for k, p in PLACES.items() if p.get("quay"))


def tide_range(t: int) -> float:
    """0 at the neaps, 1 at the springs, and back again every cycle."""
    return 0.5 + 0.5 * math.cos(2 * math.pi * t / TIDES_PER_CYCLE)


def tide_label(r: float) -> str:
    return "spring" if r > 0.85 else "neap" if r < 0.15 else "middling"


def rng_for(seed: int, tide: int) -> random.Random:
    """One stream per tide, so a run continued from a saved state is the
    same run as one played straight through — the written stays written."""
    return random.Random(f"{seed}:{tide}")


def fresh_state(seed: int) -> dict:
    g = SPECIES["gulls"]
    return {
        "seed": seed,
        "tide": 0,
        "bloom": 50,
        "herring": SPECIES["herring"]["start"],
        "shellfish": {k: SPECIES["shellfish"]["start"] for k in SHORES},
        "gulls": {k: g["start"].get(k, 0) for k in SHORES},
        "seals": SPECIES["seals"]["start"],
        "browse": {k: SPECIES["browse"]["start"] for k in SHORES},
        "deer": {k: SPECIES["deer"]["start"].get(k, 0) for k in SHORES},
        "wolves": {k: SPECIES["wolves"]["start"].get(k, 0) for k in SHORES},
        "south": 0,
        "flags": {"thin": False, "hungry": {k: False for k in SHORES},
                  "bare": {k: False for k in SHORES},
                  "deer_hungry": {k: False for k in SHORES}},
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
    r = tide_range(t)
    label = tide_label(r)
    weather = rng.choices([w for w, _ in WEATHER], [p for _, p in WEATHER])[0]
    work = WORKABLE[weather]
    spring = label == "spring"
    events: list[str] = []
    flags = state["flags"]

    if weather == "storm":
        events.append(LINES["storm"])

    # -- the bloom: stirred up by the big tides and by storms ---------
    bloom = state["bloom"] + int(35 * r) - 20 + (10 if weather == "storm" else 0)
    state["bloom"] = clamp(bloom, 0, 100)

    # -- herring: grow on the bloom, then everything eats them --------
    hs = SPECIES["herring"]
    h = state["herring"]
    h += int(hs["rate"] * (state["bloom"] / 100) * h * (1 - h / hs["capacity"]))
    if weather == "storm":
        h -= h // 20
    gulls = state["gulls"]
    total_gulls = sum(gulls.values())
    gs = SPECIES["gulls"]
    gull_fish = min(h, int(total_gulls * gs["herring_take"] * work))
    h -= gull_fish
    ss = SPECIES["seals"]
    seal_fish = min(h, int(state["seals"] * ss["fish_each"] * max(work, 0.5)))
    h -= seal_fish
    catch = min(h, int(h * CATCH_SHARE * work), CATCH_MOST)
    h -= catch
    state["landed"] += catch
    if catch >= GOOD_CATCH:
        events.append(LINES["catch"].format(place=PLACES[QUAY]["name"]))
    shoal = flags["thin"] and spring and h < hs["thin_below"]
    if shoal:
        h += hs["shoal"]
        events.append(LINES["shoal"])
    thin = h < hs["thin_below"]
    if thin and not flags["thin"]:
        events.append(LINES["thin"])
    elif flags["thin"] and not thin and not shoal:
        events.append(LINES["back"])
    flags["thin"] = thin
    state["herring"] = h

    # -- the ferry: on any tide, and owed for it ----------------------
    lo, hi = ABOARD[weather]
    aboard = rng.randint(lo, hi)
    guild = state["guild"]
    guild["crossings"] += 1
    in_news = 0
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
        s += int(shs["rate"] * (0.5 + r) * s * (1 - s / shs["capacity"]))
        if weather == "storm":
            s -= s // 20
        shore_take = 0 if weather == "storm" else min(
            s, int(g * gs["shore_take"] * (1.2 - work)))
        s -= shore_take
        gathered = min(s // 10, GATHERING[weather]) if place == QUAY else 0
        s -= gathered
        if s < shs["bare_below"] and spring:
            s += shs["spat"]
        shell[place] = max(0, s)

        fish_share = gull_fish * g // total_gulls if total_gulls else 0
        fed_on = fish_share + shore_take + (scraps if place == QUAY else 0)
        fed = fed_on / (g * gs["need"]) if g else 1.0
        born = 0
        if g and fed >= 1.0 and spring and g < gs["cap"]:
            born = max(1, int(g * gs["breed"]))
            fledged.append(place)
        lost = int(g * gs["wear"])
        hungry = bool(g) and fed < gs["hungry_below"]
        if hungry:
            lost += int(g * (gs["hungry_below"] - fed) * gs["starve"]) + 1
            if not flags["hungry"][place]:
                newly_hungry.append(place)
        flags["hungry"][place] = hungry
        new_g = max(0, g - lost + born)
        if g and not new_g:
            events.append(LINES["failed"].format(place=PLACES[place]["name"]))
        gulls[place] = new_g
    for places, one, every in ((fledged, "fledged", "fledged_all"),
                               (newly_hungry, "hungry", "hungry_all")):
        if len(places) == len(SHORES):
            events.append(LINES[every])
        else:
            events.extend(LINES[one].format(place=PLACES[k]["name"]) for k in places)

    # -- gulls move: empty shores resettle; some go off the record ----
    if weather == "calm":
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
            if back >= 5:
                events.append(LINES["north"])
        if spring:
            away = int(sum(gulls.values()) * gs["wander"])
            away = min(away, gulls[biggest])
            if away:
                gulls[biggest] -= away
                state["south"] += away
                if away >= 5:
                    events.append(LINES["south"])

    # -- seals -------------------------------------------------------
    seals = state["seals"]
    if seals:
        fed = seal_fish / (seals * ss["fish_each"])
        if fed >= 0.9 and spring and seals < ss["cap"] and rng.random() < 0.5:
            seals += 1
            events.append(LINES["pup"])
        elif fed < 0.5 and rng.random() < ss["short"]:
            seals -= 1
            events.append(LINES["seals_short"])
        elif weather == "calm" and r > 0.5 and rng.random() < 0.2:
            events.append(LINES["haul_out"])
    state["seals"] = seals

    # -- the hills: browse grows, deer graze it, wolves hunt the deer ---
    bs, ds, ws = SPECIES["browse"], SPECIES["deer"], SPECIES["wolves"]
    browse, deer, wolves = state["browse"], state["deer"], state["wolves"]
    deer_hungry: list[str] = []
    for place in SHORES:
        name = PLACES[place]["name"]
        b, d, w = browse[place], deer[place], wolves[place]
        b += int(bs["rate"] * b * (1 - b / bs["capacity"]))
        if b < bs["bare_below"]:
            b += bs["regrow"]
        graze = min(b, int(d * ds["need"]))
        b -= graze
        bare = b < bs["bare_below"]
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
        hunting = w * ws["hunt"] * ease * (1.5 - 0.5 * work)
        kills = min(d, rounded(hunting, rng))
        hunted = 0
        if (place == QUAY and weather == "calm" and d > ds["hunt_above"]
                and rng.random() < ds["hunted"]):
            hunted = 1
            events.append(LINES["table"])
        born = rounded(d * ds["breed"] * fed * (1 - d / ds["cap"]), rng) if d else 0
        lost = rounded(d * ds["wear"], rng) + kills + hunted
        hungry = bool(d) and fed < ds["hungry_below"]
        if hungry:
            lost += rounded(d * (ds["hungry_below"] - fed) * ds["starve"], rng)
            if not flags["deer_hungry"][place]:
                deer_hungry.append(place)
        flags["deer_hungry"][place] = hungry
        deer[place] = max(0, d - lost + born)

        if w:
            # judged on the hunting, not on one tide's luck: a pack goes
            # short when the deer are few, not when a night goes badly
            fed_w = hunting / (w * ws["need"])
            if fed_w >= 1.0 and w < ws["cap"] and rng.random() < ws["breed"]:
                w += 1
                events.append(LINES["cub"].format(place=name))
            elif fed_w < 0.5 and rng.random() < ws["short"]:
                w -= 1
                events.append(LINES["last_wolf" if w == 0 else "wolves_short"]
                              .format(place=name))
        wolves[place] = w
    if len(deer_hungry) == len(SHORES):
        events.append(LINES["deer_hungry_all"])
    else:
        events.extend(LINES["deer_hungry"].format(place=PLACES[k]["name"])
                      for k in deer_hungry)
    if label == "neap" and weather == "calm":
        for place in SHORES:
            if wolves[place]:
                continue
            for other in PLACES[place].get("narrows", []):
                if wolves.get(other, 0) >= ws["cross_from"]:
                    wolves[other] -= ws["crossing"]
                    wolves[place] = ws["crossing"]
                    events.append(LINES["crossed"].format(place=PLACES[place]["name"]))
                    break

    # -- the Warden writes what the Guild will not say aloud ----------
    rings = 1 + (1 if r > 0.5 else 0) + (
        1 if work >= 0.8 and rng.random() < 0.6 else 0)
    state["warden"].append([t, rings, aboard, catch])

    # -- the line ----------------------------------------------------
    clauses = list(events)
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
        clauses.append(LINES["quiet"])
    line = LINES["tide"].format(tide=t + 1, label=label, weather=weather,
                                clauses="; ".join(clauses))
    state["chronicle"].append(line)
    state["tide"] = t + 1
    return line


def run(state: dict, tides: int, out=None) -> None:
    for _ in range(tides):
        line = step(state)
        if out:
            print(line, file=out)


def summary(state: dict) -> list[str]:
    lines = [f"After {state['tide']} tides (seed {state['seed']}):"]
    for key, place in PLACES.items():
        name = place["name"]
        if place.get("unwritten"):
            lines.append(f"  {name:<40} {LINES['not_written']}")
        elif key == "sounds":
            lines.append(f"  {name:<40} herring {state['herring']}   "
                         f"bloom {state['bloom']}")
        elif place.get("shore"):
            lines.append(f"  {name:<40} gulls {state['gulls'][key]}   "
                         f"shellfish {state['shellfish'][key]}   "
                         f"deer {state['deer'][key]}   "
                         f"wolves {state['wolves'][key]}   "
                         f"browse {state['browse'][key]}")
        elif key == "skerries":
            lines.append(f"  {name:<40} seals {state['seals']}")
    lines.append(f"  {'off the record, somewhere south':<40} gulls {state['south']}")
    g = state["guild"]
    lines.append(f"  The Guild's ledger: {g['crossings']} crossings, "
                 f"{g['coin']} fares in coin, {g['news']} in news, "
                 f"{g['empty']} crossed empty and owed for.")
    lines.append(f"  Landed at {PLACES[QUAY]['name']}'s quay: "
                 f"{state['landed']} herring.")
    lines.append(f"  The Warden's ledger runs to {len(state['warden'])} lines; "
                 "--ledger shows it.")
    return lines


def ledger(state: dict) -> list[str]:
    lines = ["The Warden's ledger — what the Crown counts and the Guild "
             "will not say aloud.",
             f"  {'tide':>5}  {'rings':>5}  {'aboard':>6}  {'landed':>6}"]
    for tide, rings, aboard, landed in state["warden"]:
        lines.append(f"  {tide + 1:>5}  {rings:>5}  {aboard:>6}  {landed:>6}")
    return lines


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
            return s
    except (OSError, ValueError):
        pass
    return None


def save_state(path: str, state: dict) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(state, fh, indent=1)
        fh.write("\n")


# -- the invariants ---------------------------------------------------

def check() -> list[str]:
    """What is always true of the sandbox, or the sandbox is wrong."""
    problems: list[str] = []

    def bad(msg: str) -> None:
        problems.append(msg)

    for seed in range(1, 8):
        s = fresh_state(seed)
        run(s, 3 * TIDES_PER_CYCLE)
        if s["herring"] < 0 or s["seals"] < 0 or s["south"] < 0:
            bad(f"seed {seed}: a count went negative")
        for place in SHORES:
            for key in ("gulls", "shellfish", "deer", "wolves", "browse"):
                if s[key][place] < 0:
                    bad(f"seed {seed}: {key} on {place} went negative")
        for key in ("gulls", "shellfish", "deer", "wolves", "browse"):
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
            if PLACES["fourth"]["name"] in line:
                bad(f"seed {seed}: the chronicle spoke of Fourth Island: {line}")

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

    return problems


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--tides", type=int, default=TIDES_PER_CYCLE,
                    help=f"tides to run (default one cycle, {TIDES_PER_CYCLE})")
    ap.add_argument("--seed", type=int, default=1, help="which world (default 1)")
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
        state = fresh_state(args.seed)

    if args.history:
        if not args.state:
            print("--history needs --state: there is no past without a record")
            return 2
        for line in state["chronicle"]:
            print(line)
        return 0

    if not args.json:
        for line in companies(os.path.abspath(args.repo)):
            print(line)
        if state["tide"]:
            print(f"Continuing from tide {state['tide']}.")
        print()
    run(state, args.tides, out=None if (args.quiet or args.json) else sys.stdout)
    if args.state:
        save_state(args.state, state)

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
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BrokenPipeError:      # `| head` is a fair way to read a chronicle
        raise SystemExit(0)
