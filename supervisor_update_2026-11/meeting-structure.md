# Meeting structure: framing, questions, studies, discussion

15–20 minutes followed by discussion. This structure retains theoretical framing and
comparison to previous work in the main talk. It separates the project-level questions
from the particular experiments used to investigate them.

The [revised slides](meeting-v2.md), [HTML](meeting-v2.html) and [PDF](meeting-v2.pdf)
are a new version. The [detailed update](slides.md), [first meeting prototype](meeting-draft.md)
and [earlier structural options](presentation-options.md) remain available unchanged.

## The hierarchy

| Part | Role in the argument | What belongs here |
|---|---|---|
| **1. Framing and previous work** | Define the research problem and position it | Generation versus review; validity, acceptance, preference and requests; what earlier systems already address |
| **2. Research questions** | State the programme and the hypotheses being investigated | The structure of the review standard; finding and justifying alternatives; measuring useful review |
| **3. Experiments this month** | Report bounded evidence bearing on those questions | Three named studies, with design, observations, limits and consequences |
| **4. Open questions and discussion** | Return to the programme and decide what follows | What a justified request requires; evaluation beyond historical matching; the next discriminating test |

These are different levels. A research question is broader than any one intervention.
For example, “How can assistance improve a strong solo reviewer?” is a project question.
“Does this bank of six notes help on this developmental panel?” is one experiment.
A failed bank comparison does not answer the project question negatively.

## Part 1: retain the theoretical distinctions

The main slides introduce the objects before using them:

- **S(C, p):** changes that compile and realize the contribution purpose.
- **A(x) ⊆ S(C, p):** acceptable changes in context x = (C, p, t, k).
- **≽x:** comparative preference among viable changes.
- **D:** the requests a reviewer emits; a condition may admit several repairs.
- **Jx(r, δ):** whether asking for request r about the submitted change is justified.

The last notation comes from the existing theoretical-grounding note. It names a
judgment, not a new implemented scorer. Acceptance, preference and request-worthiness
are distinct: a contribution may be acceptable and still invite a useful suggestion;
a technically preferable edit may also be too marginal to request.

This uses the later qualifications in the maintained overview and grounding note.
Compilation alone does not establish intended purpose, an ordering does not define
an acceptance threshold, and recorded review is not the full community standard.
The original fuller formulation remains in the reference deck.

The prior-work comparison has two roles: locate related tasks, and compare mechanisms.
MathlibPR addresses merge readiness; ProofJudge compares supplied alternatives;
SWR-Bench and SWE-PRBench also study request generation. AutoCommenter, Tricorder,
Infer and RovoDev supply relevant mechanisms and measurements. Their existence rules
out treating agents, rules, retrieval or checking alone as a distinctive contribution.
Our empirical question is which interventions improve Mathlib review and why.

## Part 2: the project-level questions

| ID | Research question | This month's narrower hypothesis |
|---|---|---|
| **RQ1** | How is the community's review standard structured? | Our convention entries capture usable conditions and scope |
| **RQ2** | How can assistance improve a strong solo reviewer? | Independently acquired notes help it find and justify the right alternatives |
| **RQ3** | What establishes that a review request is useful? | Historical matching can be supplemented with independent assessment of extra suggestions |

These questions remain visible when the talk moves to experiments. The hypotheses
are not assumptions built into the definition of the task.

## Part 3: study-level reporting

| Study | Question and comparison | Evidence | Consequence for the programme |
|---|---|---|---|
| **A · Rule validity (RQ1)** | Follow flags and check them against known fixes and reconstructed scope | Some namespace flags were construct errors; genuine dot-notation departures also survived unasked | The single low-ask-rate interpretation fails; check the convention and opportunity denominator |
| **B · Knowledge transfer (RQ2)** | Same reviewer and PRs; ordinary versus compact/full notes from earlier sources | 54 reviews; none recovers the three primary concerns | This bank fails its advancement rule; the usefulness comparison remains unfinished |
| **C · Focused diagnosis (RQ2)** | A declaration and concern supplied, with/without the frozen note | 72 sessions including siblings; generalizations constructed but often declined | Generation and request choice can fail separately; this is not autonomous improvement |

Each study is labeled as a study. B and C have separate setup and result slides.
The evidence section ends by returning to RQ1–RQ3, distinguishing what changed from
what remains unresolved. Secondary historical recovery, the preparation pilot,
GPT's conditional positive and the other focused cases remain in backup.

## Part 4: discussion at the research level

Two explicit open questions follow from the framing and the evidence:

1. **Preference versus a justified request:** with a working alternative in hand, what
   evidence warrants asking for it, and when should that be optional rather than required?
2. **Historical recovery versus useful review:** how should a suggestion absent from
   the recorded review contribute to the assessment? The unjudged `dslope` proposal
   is an example to investigate, not an established improvement.

The proposed next experiment supplies alternatives to isolate the request decision.
It is labeled as proposed work. The team can challenge that priority against investing
in autonomous alternative discovery, and help choose an independent standard of value.

## Slide route and timing

| Slides | Content | Time |
|---|---|---:|
| 1–2 | Title and four-part map | 0.75 min |
| 3–5 | Task and theoretical framing | 3.5 min |
| 6–7 | Prior tasks, mechanisms and remaining gap | 2 min |
| 8 | Research questions and hypotheses | 1 min |
| 9–10 | Monthly study map and Study A | 2 min |
| 11–12 | Study B: setup, result | 2.5 min |
| 13–14 | Study C: setup, worked result | 3 min |
| 15 | Return to the research questions | 0.75 min |
| 16–18 | Open questions, proposed next test, handoff | 2.5 min |

About 18–19 minutes before open discussion. There are 18 main slides and six backups.
Section headers and colors identify the level: framing, research questions, experiments,
or discussion. The talk does not make the audience infer that hierarchy from the order.

Sources: [theoretical grounding](../docs/research/review-knowledge-transfer-grounding-2026-10-23.md),
[maintained overview](../docs/project-research-overview.md),
[review-system survey](../docs/research/code-review-systems-survey-2026-09.md),
and [experiment evidence register](evidence.md). The literature is the saved comparison,
not a newly refreshed systematic review.

Validation: the revised deck renders to HTML and a 24-page PDF. Chrome checks found
no slide overflow or header/footer overlap; the theory diagram, notation, section
transitions and main result slides were visually inspected. All 36 local links across
the revised deck, this structure note and README resolve. The October source, detailed
November reference, first prototype, earlier options and evidence register are
byte-identical to their committed versions.
