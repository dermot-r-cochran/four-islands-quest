# The Kingdom of the Four Sounds

The kingdom is named for its waters; the repository keeps its
founding name, `four-islands-quest` — there are still four islands.

A one-file browser quest engine, with a small demo world aboard.
Open `index.html` in any browser — no server, no build, no
dependencies, no network. Progress saves to that browser's
localStorage only, per chapter, and the page degrades to a fresh
start when storage is unavailable.

## What it is

Structured interactive fiction with a prose-first shape: chapters
made of **beats**, each with a quest-log stage, a presences panel,
examinable people and things, explicit choices, and a persistent
transcript. Two sidebar systems frame the story:

- **The quest log** shows the chapter's stages as they are reached,
  plus one held line for what comes next — stages ahead stay
  unspoiled.
- **Companies** is a light faction layer: factions nest (`sub` /
  `of`), keep a *seat*, carry a *quest*, and hold members. Chapters
  choose which companies stand behind them. The panel is
  descriptive — it tells the player who keeps what and why, and
  makes no rules of its own.

The engine descends from the author's earlier Evennia-based
prototypes of factions and nested inner worlds, rebuilt as a single
reviewable file: the whole world — data and engine — lives in
`index.html` and diffs cleanly in git.

World governance is deliberately minimal and lives whole in
[`WORLD.md`](./WORLD.md): the repo is the record, five spine facts
bind, everything else is soft, and no hidden canon exists.

## The demo world

Chapter One crosses the First Sound by ferry: a fare paid in coin
or news, a tide-bell nobody counts aloud, three islands worth a
fare and a fourth that pays its own way. The endcard holds **The
Second Island** open — the demo ends where your world begins.

## Extending

All content lives in four structures at the top of the script; the
engine below them never needs editing to add content.

- `CHAPTERS` — an array of `{saveId, title, sub, end, heldLine,
  beats}`. `saveId` keys the chapter's save and must be stable and
  unique; inserting chapters never orphans a save. `end` is
  `{title, text: [paragraphs], nextLabel}` — set `nextLabel` on a
  chapter when the next one exists and the endcard offers the way
  on. `heldLine` names what is not yet written.
- A **beat** is `{id, log, presences, examine, enter, choices}`:
  `log` is the quest-log stage; `presences` the who's-here list;
  `examine` an array of `EXAMINE` keys; `enter` the beat's prose as
  plain-text paragraphs; `choices` an array of `{label, text}`
  where every choice converges on the same next beat — texture,
  not branching. A beat with no choices takes an optional
  `continueLabel`.
- `EXAMINE` — `{key: {label, text}}` lookables, shared across
  chapters.
- `FACTIONS` — `{key: {name, seat, quest, members, sub, of}}`, and
  `CHAPTER_FACTIONS` maps `saveId` to the faction keys shown for
  that chapter.

Saves hold structure, not prose (`{kind, beat, choice, key}`
history entries replayed against the data), so editing text never
corrupts a save — the transcript simply re-renders from the
current data.

## License

Dual-licensed by section — see `CONTENT-LICENSE.md` for the full
statement:

- **Engine** (everything outside `index.html`'s WORLD DATA section)
  — MIT, see `LICENSE`. Fork it freely.
- **Demo world content** (the prose and data in the WORLD DATA
  section) — CC BY 4.0. Build on it with attribution, or replace it
  with your own world, which is then yours alone.
