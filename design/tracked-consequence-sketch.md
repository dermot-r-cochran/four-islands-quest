# State-tracked consequence — a design sketch

*A sketch for an experiment, written 27 October 2026 at Dermot's direction
by a Fable agent. Nothing here is settled: the engine parts are a
proposal, and every line that touches the story or the world is his
decision and is listed as one at the end. The example beat text below is
illustrative only, not proposed canon.*

*Outcome, 27 October 2026 — set down here on 29 October 2026, because a
pull request body is not a record (`CLAUDE.md`, under* Work that needs
the desktop*). The experiment was built as pull request #33 and merged
the same day. The three open choices in §6 were settled on the
recommendations given there: (a) the Carrow news runs first; (b) a fact
may change prose, presences and a choice's label and text, with the count
and order of beats and choices fixed; (a) no sign on the page beyond the
prose and the* Present *card. The gate paragraph the pull request drafted
was approved as it stands (Dermot: "Approved"), so the sentences at the
gate are his. The optional same-chapter read at the sound (§4, step 2)
was not built, which is why `tools/validate.py` warns that
`marren.knows.carrow` is set and nothing reads it: the warning is the
designed signal that the fact waits on a variant that is his pen. The
fixed test in §4 has not yet been run with readers. The sketch below is
kept as it was written.*

## 1. What the design is judged against

Dermot named the two failures. A branching story with a linear core lets a
choice colour the next paragraph and then folds every path back to the
same place; the reader learns within a chapter that nothing they do is
remembered, and stops choosing with care. A persistent sandbox remembers
everything and goes nowhere; the world is true but the story never
arrives. The engine here sits, on purpose, close to the first: every
choice converges, and `CLAUDE.md` calls that texture, not branching. The
experiment is whether a converging spine can still carry consequence.

The usual repair is a reputation score, and BrowserQuests showed why it is
weak. A scalar throws away the three things that make a consequence feel
earned: *who* knows, *what* they know, and *when* they came to know it.
Every good deed and every bad one lands in the same number, so every
consequence reads the same (a warmer greeting, a cheaper price), the reader
cannot trace a result back to a cause, and once the meter is visible they
play the meter rather than the people. The alternative is to track facts
held by named holders, so that a consequence can only ever arrive as a
named person saying or doing a particular thing because of a particular
earlier choice.

## 2. The state model

**A fact is one short string with three parts: `holder.verb.thing`.** The
holder is a person or an island as the prose already names them
(`marren`, `warden`, `porter`, `first`, `second`). The verb is one of a
tiny closed set, and I would start with three: `knows` (was told),
`saw` (witnessed), `owes` (is in your debt; `you.owes.marren` for the other
direction). The thing is a free word the author chooses. That is the whole
vocabulary. There are no values, no counts and no scores; a fact is held or
it is not.

**Time is the chapter.** The engine has no clock and should not grow one.
A crossing is a chapter, and news goes as the boats go, so a fact may carry
a delay in chapters: `second.knows.carrow+1` becomes true one chapter after
the choice that set it. The author writes the boat's speed into the fact;
nothing is simulated.

**A choice sets facts; a beat or a choice reads them.** Two optional keys,
no new top-level structure:

- `sets: [facts]` on a choice. Taking it adds those facts.
- `variants: [{when: [facts], ...}]` on a beat or a choice. The first
  variant whose `when` list is wholly held replaces the fields it names
  (`enter`, `presences`, `examine`, a choice's `text` or `label`); the
  unnamed fields and the default stand. An `unless` list is the only other
  operator worth having, and I would leave it out until a chapter needs it.

Facts are never saved. They are derived, every render, by replaying the
saved histories of all chapters in order and collecting what each chosen
choice `sets`, with delays measured from the chapter that set them. Saves
keep their present shape (`{kind, beat, choice, key}`); restarting a
chapter withdraws the facts it set, as it should; and nothing in
localStorage can drift from the data.

Three examples in the file's own format, extended by one key each. The
prose in them is a placeholder to show the shape.

```js
// Chapter One, the quay — the existing second choice, plus one line
{
  label: "Offer news instead.",
  text: [ /* unchanged */ ],
  sets: ["marren.knows.carrow", "first.knows.carrow+1"]
}
```

```js
// Chapter One, the sound — the existing first choice, plus one line
{
  label: "Ask about Fourth Island.",
  text: [ /* unchanged */ ],
  sets: ["marren.saw.you-point-south"]
}
```

```js
// Chapter Two, the gate — the beat as it is, with one variant
{
  id: "gate",
  log: "The gate of the High Keep",
  presences: ["the porter", "the gate", "the arch"],
  enter: [ /* unchanged */ ],
  variants: [
    {
      when: ["first.knows.carrow"],
      enter: [
        "…(illustrative) the porter had heard, from a carter who had it " +
        "from the quay, that Carrow's bridge was down again, and looked " +
        "at you as the likeliest source…"
      ]
    }
  ],
  choices: [ /* unchanged */ ]
}
```

An author writes nothing but strings and lists, which is the test the
prime directive sets.

## 3. How consequence reaches the page

A later beat changes because a named holder holds a named fact: the porter
speaks of Carrow only if First Island has heard it, and First Island has
heard it only if Marren was told it a chapter ago. The reader sees the
porter's line, remembers the quay, and can name the chain themselves.

The spine stays whole because a variant can change what a beat says and
who is present, and cannot change the shape of the chapter. Beats are
never added, removed or reordered by a fact; a variant may reword a
choice's label and text but never changes the count or order of choices;
every path still converges on the same next beat. Progression therefore
cannot stall, since no fact is ever needed to go on, only to be spoken to.
That also keeps saves safe: positions are unchanged under every variant,
and a history replayed against a different set of facts simply re-renders
the same positions with different words, which is the engine's existing
rule that saves hold structure and not prose.

The reader can tell a choice mattered without a meter because the sign is
diegetic and specific. The transcript already keeps the earlier choice on
the page above; the later line names the earlier thing (Carrow, the finger
pointed south, the rings counted aloud); and the *Present* card can carry a
person who is only there because of what they know. Nothing new is drawn
in the sidebar. If a reader cannot work out which choice produced a line,
the line has failed, and the repair is better prose, not a display.

## 4. The smallest experiment

One chain, inside the two chapters that exist, touching three beats:

1. Chapter One, *the quay*: "Offer news instead" sets
   `marren.knows.carrow` and `first.knows.carrow+1`. "Pay the coin" sets
   nothing.
2. Chapter One, *the sound*: Marren's second reply could carry a variant on
   `marren.knows.carrow` (he has a reason to be generous). This is optional
   and shows a same-chapter read with no delay.
3. Chapter Two, *the gate*: the porter's `enter` carries a variant on
   `first.knows.carrow`, which is true only because a chapter has passed.
   On "Pay the coin" she says what she says today.

The test, fixed before anything is played: three playthroughs (coin then
bridge; news then bridge; news then wood), and after each a reader who has
not seen the data is asked two questions — *did anything at the gate depend
on the quay, and if so which choice?* **Success** is that the news
playthroughs are traced to the quay by name, the coin playthrough is not
claimed to have a consequence, and no beat count or choice count changed.
**Failure** is any of: the variant reads as flavour that could have come
from either choice; the reader needed to be told there was a system;
delivering it needed a new beat, a new structure or a change to `teller/`.
A partial result (traced, but only because the porter quotes the choice
word for word) is a prose failure, not a design failure, and says the
mechanism needs a better author rather than a better mechanism.

The chapter prose that would make this real is his pen. The sketch only
claims that the three beats above are where the chain would sit.

## 5. What it costs the engine

`index.html`, engine section, roughly five small functions and two touched
ones, all below the data:

- `heldFacts()` — replay every chapter's saved history in `CHAPTERS` order,
  collect `sets` from each chosen choice, apply `+N` delays against the
  chapter index now open, return a `Set`.
- `holds(facts, list)` — every atom in `list` is in the set.
- `pick(node, facts)` — the first matching variant merged over `node`, or
  `node` itself. Pure; no side effects.
- `renderHistoryEntry` and `renderActions` call `pick` on the beat and on
  each choice before reading `enter`, `presences`, `examine`, `label` and
  `text`; `renderPresences` does the same. Nothing else changes, and
  nothing is written to storage that is not written today.

One decision I would make rather than leave open: facts are derived, not
recorded in history. Recording the chosen variant index would freeze a
past page against a later restart of an earlier chapter, which is the one
case where derivation re-tells the past; I think re-telling is the right
behaviour here (the past is what the record now holds), and it keeps the
save shape untouched, but it is worth saying aloud.

`tools/validate.py` is byte-identical with its sibling, so the checks must
be about shape and never about this world's words, which they can be:

- every `when` atom is set by some `sets` somewhere (fail);
- every `sets` atom is read by some `when` (warn, like an unlooked-at
  examinable);
- an atom is `word.word.word` with an optional `+N`, `N` a whole number,
  and the delay never reaches past the last chapter (fail / warn);
- a condition is meetable: every atom it names is set in an earlier chapter
  — or, with `+N`, at least `N` chapters earlier — or earlier in the same
  chapter at a beat before the reading one (fail);
- a variant names no field the node lacks and never changes the number of
  choices (fail);
- the existing scripted first-choice walk still reaches every endcard.

`teller/` is not touched. It will play the default text of every beat,
which is a complete and correct story, and the day somebody wants
consequence in the terminal the same `pick` is a dozen lines of Python
beside `questfile.py` — but that is a change to a shared tool and a
separate decision.

## 6. Open choices for Dermot

**Which chain runs first.** (a) The Carrow news, Marren to the porter, as
above. (b) The ring count: in *landfall* you answer the Warden truthfully
and the ferry draws breath, so `marren.saw.you-count-rings` is already
written into the prose and waiting. (c) The bridge ledger: the keeper wrote
your name and the porter already reads your boots. I would recommend (a).
It is the only one with a boat and a delay in it, it needs two named
people who are both already on the page, and it touches no spine fact,
where (b) stands next to *the bell is not counted aloud* and would need
care the first experiment should not have to take.

**What a fact may change.** (a) Prose and presences only. (b) Also a
choice's label and text, count fixed. (c) Also which examinables a beat
offers. I would recommend (b), with (c) harmless but unneeded yet: the
texture of a choice is where this engine already does its work, and a
label that acknowledges what a person knows is a consequence the reader
cannot miss, while adding or removing a choice would be the first step
back towards branching.

**The sign on the page.** (a) Nothing beyond the prose and the *Present*
card. (b) A line at the foot of the quest log naming what is known of you
so far ("Marren has the Carrow news"). I would recommend (a), on the basis
of his own objection to the generic score: a list of known facts is a
better meter, but it is still a meter, and the experiment is whether the
story can carry the weight alone. If the fixed test fails on the question
of whether readers noticed, (b) is the cheapest second attempt and is a
display change only.

None of the three is needed to begin building the engine side; the first
two settle what the experiment's three beats say, and that is his pen.
