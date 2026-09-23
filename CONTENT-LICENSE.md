# Content License

This repository is licensed by section, so the engine can be forked
freely while the demo world's writing carries attribution and its
pictures stay the author's.

## Engine — MIT

Everything outside the WORLD DATA sections of `index.html` and
`sandbox/ecosystem.py` — the engine script, page markup, styles, the
`teller/` terminal player, the sandbox's engine, `tools/`, and
repository scaffolding — is licensed under the MIT License. See
`LICENSE`.

## Demo world content — CC BY 4.0

The story content of the demo world — the prose and world data in
`index.html`'s WORLD DATA section (`CHAPTERS`, `EXAMINE`, and
`FACTIONS`: chapter text, choice text, examinable descriptions,
company descriptions, and their names), together with the WORLD DATA
section of `sandbox/ecosystem.py` (its places, species, and chronicle
lines) — is licensed under the Creative Commons Attribution 4.0
International license (CC BY 4.0):

https://creativecommons.org/licenses/by/4.0/

You may share and adapt the demo content, including commercially,
provided you give appropriate credit, link the license, and indicate
if changes were made. Suggested attribution:

> Demo world by Dermot Cochran, from *four-islands-quest*
> (https://github.com/dermot-r-cochran/four-islands-quest),
> CC BY 4.0.

## Pictures and clips — CC BY-NC-ND 4.0

The images in `reference/` and the clips in `media/` — and any picture
the record names in a chapter or on a generated page — are the
author's own work and carry their own terms: the Creative Commons
Attribution-NonCommercial-NoDerivatives 4.0 International license
(CC BY-NC-ND 4.0):

https://creativecommons.org/licenses/by-nc-nd/4.0/

You may share them unchanged, with credit, for non-commercial
purposes. You may not adapt them — no crops, re-colouring, upscaling,
re-generation from them, or use as training or reference material for
a model — and you may not use them commercially. Suggested
attribution:

> Picture by Dermot Cochran, made with Grok, from *four-islands-quest*
> (https://github.com/dermot-r-cochran/four-islands-quest),
> CC BY-NC-ND 4.0.

Name the tool that `reference/README.md` records for the file; every
picture filed there so far was made with Grok. A generated picture is
credited as generated, so nobody takes it for a photograph or a
painting (the author's decision, 23 September 2026).

A note on what this section can and cannot do. Where a picture was
generated rather than photographed, how far copyright reaches over it
varies by country and is not settled law: some jurisdictions recognise
an author in whoever made the arrangements for the work, while others
hold that output produced from a prompt has no human author at all and
protect only a person's own contribution to it — the choice of frame,
the editing, the arrangement. So this section is best read as a
statement of the terms the author asks for, which holds wherever there
is a right to license and states his intent where there is not. It
asserts nothing about which of those a given file falls under, and a
reuser is not invited to guess: ask.

Separately, and regardless of copyright, the terms of the service that
generated a picture may bind its use. `reference/README.md` records
which generator made each file for that reason.

This section is the terms for the files, not a rule about the world:
what the record says about a picture stays soft world content like
everything else, under the section above.

## The intended fork path

Fork the engine, then either build on the demo world (with
attribution, as above) or replace the WORLD DATA sections wholesale
with your own world — a world you write yourself is yours alone, and
only the MIT engine terms apply to it.

The pictures go the same way as the world data, and have to: a fork
that keeps them is bound by CC BY-NC-ND, which forbids the adaptation
a new world would want and any commercial use of it. So a fork
replaces the pictures as it replaces the prose, and then owns what it
puts there.
