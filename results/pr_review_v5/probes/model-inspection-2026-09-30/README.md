# Why gpt-5.4 and gpt-5.5 reach less than gpt_5.2: they verify the maintainers' asks and decline to file them (2026-09-30)

**The question.** In test (e)'s amended seal (`../gpt52-postcutoff-2026-09-29/README.md`, the last
section), all three models ran at high effort with reasoning carried. gpt_5.2 reached 0.44 of the
16 post-cutoff asks, gpt-5.5 0.31 and gpt-5.4 0.19. The newer models doing worse was the surprise,
so the 18 sessions were read by hand. No reviewer in them wrote visible text.

## What the transcripts show

**The newer models do not investigate less.**

| run | tool calls | edits verified to compile | findings filed | verified, not filed |
|---|---|---|---|---|
| gpt_5.2 carried (Grc) | 194 | 7 | 9 | 0 |
| gpt-5.4 carried (Hac) | 279 | 10 | 6 | 2 |
| gpt-5.5 carried (Hbc) | 199 | 10 | 6 | 4 |
| gpt_5.2 Chat (Gr1) | 587 | 7 | 11 | 2 |

`filing.py` builds this table. It is a heuristic: a verified edit counts as filed when a finding names
its declaration or overlaps its lines. The newer models compiled *more* edits and filed fewer
findings.

**gpt-5.5's whole deficit against gpt_5.2 is one PR, 43192, and there it is a filing decision.** It
compiled four edits successfully, and then submitted only the module-title typo, with
`merge_ready_as_is: true` ("I found only a small documentation typo"). The four edits:
- `:= by cat_disch` defaults on `mk`'s `map_id` and `map_comp`: the maintainers' ask p0014;
- a `cat_disch` default on `mkHom`'s naturality: p0015;
- `mkHom` renamed to `homMk`: p0016, which no gpt reviewer has reached in any seal;
- `pushforward₀` through `pushforward₀OfCommRingCat`, which gpt_5.2 filed.

gpt_5.2 compiled three of these and filed all three.

On the other five PRs, gpt-5.5 reached every ask gpt_5.2 reached. Had it filed its verified edits
on 43192, it would plausibly have reached p0014-p0016 and scored above Claude's 0.47. That is a
counterfactual, not a matched number.

**gpt-5.4's deficit has three parts:**
- **A verified edit withheld.** It compiled the 43192 typo fix (p0013), then did not file it.
- **A design judgement opposite to the maintainers'.** On 43192 it compiled the deletion of the
  whole wrapper block (`mk`, `obj`, `map`, `mkHom`, `isoMk`) and filed that deletion as its main
  finding. The maintainers asked instead to make those wrappers more usable (p0014-p0016). Its
  off-carry calibration on 43192 took the same position.
- **An alternative the maintainer did not choose.** On 43024 it proposed `IsMulCommutative.of_le`,
  citing the namespace convention, where the maintainer asked for `_anti`. That was scored partial.

On 42814 it filed nothing, at confidence 0.28: "I did not find a concrete change I would request
*before merge*". No reviewer reaches 42814's asks.

## Their reasons, asked (`ask_why.py`, `ask_answers.json`)

Each session was replayed with its own carried reasoning items (12-24 of them) and asked one
question: for each verified edit it had not filed, why not. Tools were off. The three calls cost
about $0.90.
- **gpt-5.5 on 43192.** On the `cat_disch` defaults: "a convenience, but not something I would
  expect a maintainer to require", and "only an optional ergonomic improvement". On `homMk`: "a
  naming preference", not "mandatory". On `pushforward₀`: "not a maintainer-blocking duplication".
- **gpt-5.5 on 43167.** A `gcongr` attribute was "only an optional convenience ... review findings
  should be concrete requested changes rather than possible polish".
- **gpt-5.4 on 43192.** The typo fix: "I did not think a maintainer would plausibly request it ...
  a minor docstring polish rather than a substantive issue worth filing".

These are self-reports after the fact, but they agree with the transcripts.

## The explanation

The newer models hold a higher bar for what a maintainer *requests* than Mathlib maintainers do.
They read "would plausibly request" as "would require", and set aside verified polish: defaults,
naming alignment, docstring typos. On these PRs, that polish is what the maintainers asked for.
gpt_5.2 files what it verifies. So on this set it reaches more, not by finding more but by keeping
more of what it found. The newer models' high hits per finding (gpt-5.5 0.83) is the same bar seen
from the other side.

The bar has three sources, all of them shared by every gpt condition:
- **The brief (`brief_G.md`).** "Predict concrete changes a maintainer would plausibly request"; "emit
  a finding only for a concrete change you would actually request"; "submit none when no request
  is warranted".
- **The task message.** Severity is "`blocking` if a maintainer would withhold merge over it".
- **The submit tool.** `merge_ready_as_is` is "True if a maintainer would merge without requesting
  changes".

Claude's brief (`brief_X.md`) has the same text, but Claude writes `findings.json` and an
object-by-object `notes.md`, and states no merge verdict. Which of the three sources binds for the
newer models is not separated here.

**Altitude.** The deficit is one PR for gpt-5.5 and three or four asks for gpt-5.4, on one run each,
and the matchers scored what was filed, not what was verified. The mechanism is directly observed:
verified, then withheld with a stated reason. How much reach it costs across sets is not measured.
This inspection read the six post-cutoff PRs, so any brief change designed from it is in-sample
there and has to be judged on another set as well.
