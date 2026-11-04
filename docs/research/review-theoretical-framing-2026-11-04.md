# Theoretical precedents for the review framing

Targeted literature search, 4 November 2026, prompted by the supervisor-update
discussion. This is not a systematic review. It does not modify the presentation.

The question is whether there is an established account resembling our working
framing: automated checks help distinguish solutions from non-solutions; human
review identifies acceptable or preferred contributions; automating some of that
judgment extends what the combined system can check.

## Closest explicit theoretical model

**Gonçalves, Rani, Storey, Spinellis and Bacchelli (ICPC 2025), _Code Review
Comprehension: Reviewing Strategies Seen Through Code Comprehension Theories_.**
[DOI](https://doi.org/10.1109/ICPC66645.2025.00068) ·
[Open paper](https://arxiv.org/abs/2503.21455)

The authors extend Letovsky's code-comprehension model into a **Code Review
Comprehension Model**, using observations/interviews of ten experienced reviewers
across 25 review sessions. Their model distinguishes information sources, the
reviewer's knowledge base, and mental models of the change. It explicitly treats
reviewers as comparing the actual implementation with **expected and ideal
solutions**. They use self-discrepancy theory to interpret those alternatives.

Section IV-C3, “The Expected and the Ideal,” is especially relevant. Expected
models can reflect prior agreement, previous review rounds and engineering
practice. Ideal models describe an improved or optimal version, informed by
experience, preferences and good practices. Following the ideal is valued but
not always required: a reviewer can accept a different solution that solves the
problem without adding technical debt.

This is a close precedent for both the acceptance/preference distinction and the
comparison hypothesis. It is a cognitive/descriptive model, not a set-theoretic
definition of acceptance or proof that review obeys a global partial order.
Expected and ideal mental models also need not be fully implemented alternatives.
Our independent whole-contribution reconstruction experiment tests one operational
interpretation, not the full scope of this model.

## Direct ICSE support for automating part of review

**Bacchelli and Bird (ICSE 2013), _Expectations, Outcomes, and Challenges of
Modern Code Review_.**
[DOI](https://doi.org/10.1109/ICSE.2013.6606617) ·
[Microsoft Research and paper](https://www.microsoft.com/en-us/research/publication/expectations-outcomes-and-challenges-of-modern-code-review/)

Their empirical account separates finding defects, code improvement, alternative
solutions, knowledge transfer and other benefits. Code improvement explicitly
includes team conventions and changes that do not concern functional correctness.
Code/change understanding is central to the review process.

Section VII-B has a recommendation headed **“Automate Code Review Tasks.”** It
specifically discusses automating team-convention enforcement and other recurring
checks, freeing reviewers for deeper issues. This directly supports automating a
subset of human review, rather than treating that research goal as a new insight.
The paper supplies a conceptual/empirical account, not our S/A/R formalization.

**Sadowski et al. (ICSE-SEIP 2018), _Modern Code Review: A Case Study at Google_.**
[DOI](https://doi.org/10.1145/3183519.3183525) ·
[Google Research and paper](https://research.google/pubs/modern-code-review-a-case-study-at-google/)

Sections 7.2 and 8 connect automation and community practice particularly clearly:
static-analysis integration lets reviewers concentrate on understandability and
maintainability, while review establishes and evolves norms for readability and
consistency. Ownership and language-readability approval also make different
review responsibilities explicit. The analyzer's presence does not make all its
findings mandatory: the paper describes “Please fix” and “Not useful” feedback.

This is a strong empirical account of a division of work between automation and
human review, and of review as maintaining an evolving shared standard. It is
an industrial case study, not a formal theory identifying a unique acceptance set.

## An explicit acceptance principle from practice

**Google Engineering Practices, _The Standard of Code Review_.**
[Primary source](https://google.github.io/eng-practices/review/reviewer/standard.html)

This is guidance, not a conference paper. It nevertheless supplies a more explicit
normative acceptance rule than the case studies: approve changes that improve
overall code health, balancing progress and the importance of proposed revisions,
without demanding perfection. Nonessential improvements can be marked optional.
Its principles distinguish technical evidence, written style rules, consistency
with the existing codebase and valid alternatives among which the author's choice
can stand.

This is useful support for saying that a preferred alternative can exist while
the current contribution is acceptable. It is Google's stated standard, not a
universal account of how Mathlib maintainers actually decide.

## Related traditions and their limits

- **Fagan (IBM Systems Journal, 1976), _Design and Code Inspections to Reduce
  Errors in Program Development_.** [DOI](https://doi.org/10.1147/sj.153.0182).
  The foundational inspection account uses defined exit criteria, error classes,
  systematic detection and rework/follow-up. It is a historical precedent for
  additional review criteria governing progress through a development process.
  Only the indexed abstract and its treatment in the survey below were checked
  here, so it should not be cited for a stronger claim about preference ordering.
- **Endres et al. (APR 2022), _What Can Program Repair Learn from Code Review?_.**
  [DOI](https://doi.org/10.1145/3524459.3527352). The indexed abstract explicitly
  distinguishes correctness and acceptability of plausible generated patches,
  and proposes importing review practices into repair evaluation. This is adjacent
  support, not a reviewed full-text basis for our account; full text was inaccessible.
- **Hentschel, Hähnle and Bubel (IFM 2016), _Can Formal Methods Improve the
  Efficiency of Code Reviews?_.**
  [DOI](https://doi.org/10.1007/978-3-319-33693-0_1). Full text checked. The work
  uses symbolic execution to help human program understanding and defect detection.
  It illustrates that formal analysis and review can cooperate, but is not a theory
  of acceptance or community conventions. Its title should not be mistaken for one.
- **Badampudi, Unterkalmsteiner and Britto (TOSEM 2023), _Modern Code
  Reviews—Survey of Literature and Practice_.**
  [DOI](https://doi.org/10.1145/3585004) ·
  [Open version](https://arxiv.org/abs/2403.00088). Full text searched as a map
  to earlier work, not as proof that no other theoretical account exists.
  It surveys 244 primary studies through 2021; it cannot cover the ICPC 2025 model.

## Implications for the supervisor update

Anchor the opening in the ICPC model and ICSE accounts. The underlying ideas that
review evaluates more than functional correctness, compares actual and better
solutions, and can be partly automated have clear precedents. Our S, A_t and S_R
notation is a way to organize the research question, not a claimed established
formalism from these sources. This search did not establish an exact matching
published formalization, and cannot establish novelty of that notation or idea.

The useful project-specific question is which parts of this human judgment can
be recovered and made operational for Mathlib: which conventions hold, what
evidence supports their application, which differences warrant requests, and
whether the resulting system improves review.

The division between checks and humans should be described as overlapping.
Reviewers also discover functional failures and missing requirements; static
analysis can already enforce some style and maintainability rules. Passing
existing checks is evidence, not complete certification of task fulfillment.
Automating review should reject more unacceptable contributions while avoiding
new unwarranted rejections, and preserve advisory improvements as a separate role.

## Verification

Bibliographic discovery used Crossref and OpenAlex, followed by primary full-text
reads of the ICPC 2025, ICSE 2013, ICSE-SEIP 2018 and IFM 2016 papers, targeted
search of the TOSEM survey, and the live Google standard. Metadata/abstract-only
sources are marked above. PDFs and extracted text were kept under
`/tmp/review-theory-literature`, not added to the repository. No model generation,
semantic judging or experimental runs were performed. Presentation files were
not edited during this search.
