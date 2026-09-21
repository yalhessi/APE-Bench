# What an LLM adjudicator would be asked, and how we would know it was any good

**Status** — open; the socket is built (2026-09-21), the rubric is not
**Cost** — no spend to design; a validation sitting costs ~30 human labels and one cheap run
**Owner question** — can a model tell "true and not something a maintainer would raise" from
"the maintainer would have raised this", well enough to order a queue?

## Motivating example

~90% of what the system emits is off-gold, and nothing adjudicates it. `gold_alignment_rate` is
not precision -- gold is a lower bound, so a finding absent from it is *unaligned*, not wrong --
and the batching comparison moved alignment **0.069-0.091 → 0.181-0.202** and control emission
**2/3/4 → 0/0/1** with nobody able to read either as better output
(`docs/todo/README.md`, "Adjudicating findings that are not maintainer obligations").

`cli adjudicate` now keys those findings and carries labels across runs: on
`heldout12_v2_rep1`, **259 unadjudicated findings over 214 distinct keys**, 45 of them sharing
a key with a sibling. The store takes `labelled_by: task:<identity>` beside `human:<name>` and
a human row outranks a model's, so an adjudicator plugs in without moving anything. What is
missing is the only hard part: what it is asked, and how we would know its answers are worth
keeping.

## What would close it

1. **A rubric that distinguishes three verdicts, not two.** `valid_not_an_ask` is the one that
   matters and the one a correct/wrong split destroys -- Tricorder's definition is built on
   exactly that distinction, and Atlassian's result is the warning: a factual-grounding judge
   did almost nothing there, while a value/actionability gate trained on whether comments were
   resolved moved 15-20pp (`code-review-systems-survey-2026-09.md`). Truth is not the question.
2. **Human labels first, and enough of them.** The store exists so that ~30 labels can be
   written once and reused. Agreement between the model and those labels is the gate, and it
   has to be measured on the `valid_not_an_ask` boundary specifically, because that is where
   the judgement is.
3. **Its own version and its own identity.** `ADJUDICATION_VERSION` is separate from the schema
   version already. Whatever task runs it needs its own `task_type` so it can never resume into
   the semantic judge's cache -- `judge_version` is in that cache key for the same reason.

## Risk

This is the judge-grades-judge circularity the benchmark was built to avoid, one step removed.
Gold's whole worth is that it is revealed preference: what maintainers actually asked for,
model-independent. An adjudication label is a judgement about what they did *not* ask for, and
it must never be folded into gold, counted in recall, or reported as precision. Its legitimate
use is to **order a queue** -- which findings a person should read first -- and to say how much
of the output has been read at all.

The second risk is cheaper to state: a label keyed by site and kind stands for whatever share
of findings reproduce that key, and 45 of 259 on one run share a key with a sibling. The report
prints that; a rubric study has to respect it, or one verdict will silently cover two asks.
