# Restructuring the monthly check-in

Working brief: 15–20 minutes, then discussion, for a team following the project roughly
once a month. They need to recover the research question, understand what changed since
last time, and help choose the next investigation.

The [37-slide detailed update](slides.md), its renders, and [evidence register](evidence.md)
remain unchanged as reference material. The [meeting draft](meeting-draft.md) is a separate
prototype of option A below, with [HTML](meeting-draft.html) and [PDF](meeting-draft.pdf).
The theoretical expansion is still a later task.

## What is getting in the way

The detailed update is organized for checking the research record. It asks the audience
to do too much of the interpretation while listening:

- The experimental account starts on slide 14, after formalization and a literature survey.
  That spends much of a monthly meeting recovering background before reaching the progress.
- Many slides combine the question, several interventions, results, caveats and a conclusion.
  The audience must read those while the speaker explains them.
- The comparison changes repeatedly: models, samples, instructions, stages and units of
  measurement. Tables put these on screen before establishing what the experiment tests.
- The experiment list obscures why one result led to the next experiment. A listener sees
  many negative readings without a clear account of the knowledge gained.
- Open questions arrive as recommendations at the end. The team needs an explicit choice
  to weigh, including what the next test would and would not resolve.

Reducing the font or shaving words would retain these problems. The spoken route needs
its own selection and order. Detailed evidence remains available through notes and references.

## Three viable structures

| Option | Spoken route | Strength for this meeting | Tradeoff |
|---|---|---|---|
| **A. Questions and answers — recommended** | Last month's open question → three investigations → what changed → next decision | Makes the month's intellectual progress visible, including what negative results taught us | Secondary experiments move to backup; the talk does not enumerate every run |
| **B. One case as the spine** | Introduce the generality example → show successive attempts to recover the request → zoom out to the broader studies | Gives the audience a concrete object to follow throughout | A familiar selected PR can appear more representative than it is; generality does not illustrate every convention failure |
| **C. The sequence of research decisions** | We suspected missing knowledge → checked the rules → tested notes → narrowed the task → reconsidered the decision | Makes the work and decisions since the last check-in easy to follow | Can become a lab diary unless each step immediately answers “what did this change?” |

I recommend A, with the generality example borrowed from B and the causal links in C made
explicit in the speaker notes. It gives the team enough experimental design to challenge
the conclusions without requiring it to reconstruct the whole execution history.

## The proposed spoken route

Each investigation gets a question, a comprehensible comparison, an observation and a
consequence. The main bank study and focused follow-up each use separate setup and result
slides so the speaker can establish the contrast before asking the audience to read it.

| Slide | Purpose | Approx. minutes |
|---|---|---:|
| 1. Can we turn convention knowledge into better review? | State this month's question | 0.5 |
| 2. Last time, supplying the right convention helped | Recover the earlier result and its unresolved limitation | 1 |
| 3. We investigated three questions | Give the audience a route through the experiments | 0.75 |
| 4. Our flags mixed different situations | Explain the rule-validity correction through two contrasting findings | 1.75 |
| 5. Would notes from other PRs improve review? | Show the common setup and the three changed inputs | 1.5 |
| 6. The three target requests were still missing | Give the primary result before discussing secondary changes | 1.5 |
| 7. Next we narrowed the reviewer's question | Establish the focused diagnostic and its different task | 1 |
| 8. A working generalization was often declined | Walk through one actual example and the observed choices | 2 |
| 9. The other cases stopped at different stages | Show the limits of a single explanation | 1 |
| 10. We can now separate two kinds of miss | Explain what the experiments changed in our diagnosis | 1 |
| 11. Could useful suggestions be missing from our score? | Introduce the concrete unresolved evaluation problem | 1 |
| 12. Proposed next: test decisions with a candidate supplied | Make the proposed next investment and its limits concrete | 1.5 |
| 13. Where should we invest next? | Invite two specific team decisions | 0.5 |

About 15 minutes of planned explanation leaves room within 20 minutes for transitions
and short interruptions, then a longer discussion. Slide 8 is the place to slow down:
the audience should understand the change being proposed before weighing the rejection.
If time runs short, move slide 9 to backup; preserve the discussion.

## How the experiment slides change

The main comparison should be visible without reading the notes. “Same PR, same reviewer,
same tools; change only the supplied notes” is a useful diagram. A table of nine metrics
is not the first explanation of that experiment.

Use one primary observation on the result slide. For the bank comparison that is the
absence of all three target concerns across the three conditions. The broader historical
recovery table stays in backup, with an explicit reminder that the full notes did recover
some other asks. This avoids silently turning a failed advancement rule into an overall
claim that nothing improved.

For the focused study, show the declaration and proposed change before the score. In the
generality example, a parameter replaces the constant 2 while the special case remains
available. All six focused sessions built a checked generalization; their recommendations
differed. The actual reason for declining then becomes a meaningful object of discussion.

Report a short limit with each result when it changes its meaning: selected cases;
concerns supplied; usefulness unfinished; a failed tool on one pilot PR. Exact run identities,
matcher details, all denominators and further corrections remain in the speaker notes
and evidence register. The audience should hear the material limit even if it never opens
those documents.

## What stays available

| Material in the detailed update | Place in this structure |
|---|---|
| Task formulation and literature, slides 2–11 | Preserved reference; brief spoken recap only if needed; theory still awaits its own revision |
| Solo/decomposition/model baselines, slides 12–16 | Reference for questions about the baseline; no repeated model leaderboard in the main talk |
| Census, exact supply and ask-free selection, slides 17–21 | Main recap plus backup for the GPT disposition positive |
| Rule validity, practice and stated reasons, slides 22–24, 34 | One main correction; exact counts and grounds remain in reference |
| Conditional-preparation pilot, slide 25 | Backup: its null result and environment limit are both retained |
| Bank and focused studies, slides 26–30 | Main evidence, with setup/result separated and one worked case |
| Exploratory suggestion and current question, slides 31–33 | Main evaluation question and proposed next decision |
| Infrastructure and evidence, slides 35–37 | Reference and source links; infrastructure supports the experiments rather than standing in for review progress |

The prototype has 13 main slides and four backups. Its notes include the transitions and
important limits. It is an option for reviewing the structure together, not a replacement
of the detailed update or a claim that the next study is already agreed or registered.

Local checks: both presentation formats render, with 17 PDF pages and no slide overflow
or header/footer overlap in Chrome. The setup, primary result, worked example and discussion
slides were visually checked. The 0/9 primary counts agree with both saved matching tables;
the detailed slide source and evidence register remain byte-identical to the prior commit.
