# Response to the 14 October 2026 version-2 review

Revision date: 15 October 2026. Revised output: version 3.0. This is an author-side response and traceability record, not a reviewer verdict, peer-review decision or REF rating. The earlier version-1 response is preserved as `RESPONSE_TO_REVIEW_V1.md`.

## Revision checklist

| # | Review issue | Resolution | Location | Status |
|---|---|---|---|---|
| R1 | The separate checker trusted certificate domains instead of independently connecting them to the declared model. | The checker now rebuilds 16 audited domains and all 10 trigger regions directly from `contracts.json`, checks strict-branch reachability and equality ownership, and minimises over the reconstructed domains. A self-consistent shortened-domain mutation is retained and rejected under ordinary and optimised Python. | `code/check_certificates.py`; `code/test_revision.py`; manuscript §15.1 and coverage matrix | RESOLVED |
| R2 | The rich example exercised implementation more strongly than substantive design because old PV/duration matched, later payments were proportional, and the oblique trigger cancelled from the cap. | Added an exact parameter family with unmatched old PV/duration and nonproportional later streams. The oblique trigger switches the binding constraint from programme service to duration; the cap is 25 off-trigger and 110/7 on-trigger, with the exact family switch at uplift 75/7. | `data/contracts.json`; `code/verify.py`; `code/check_certificates.py`; manuscript §12.4 | RESOLVED |
| R3 | A perturbation could show the endpoint failure is not an equality artefact. | Added and proved the family `4 d1 d3 [x(x-1)+eta]`, with both endpoint margins strictly positive and the midpoint negative for every `0 < eta < 1/4`; `eta=1/8` is retained as an exact regression. | manuscript §5; `code/test_revision.py` | RESOLVED |
| R4 | “Two-state” was inaccurate for a continuum with two state variables. | Replaced with “two-state-variable” in the abstract and section heading. | abstract; manuscript §12 | RESOLVED |
| R5 | Markdown and HTML bibliographies lost author/year labels. | Replaced LaTeX description-list labels with explicit paragraph labels, then regenerated and checked the accessible Markdown and HTML. | manuscript source and distributed conversions | RESOLVED |
| R6 | Implementation scope needed to distinguish the mathematical class from the executable conventions and low-dimensional checker. | The README, manuscript and assurance file now state the integer-date/rational-rate executable scope, the general fixed-positive-rational mathematical scope, and the checker's one-/two-dimensional boundary. | README; manuscript §§3, 13 and 15; ASSURANCE | RESOLVED |
| R7 | Revision-history and assessment material distracted from the scientific output. | Replaced the manuscript's review-history subsection with a self-contained account of input, domain and certificate binding. Review chronology remains in response records rather than the scientific argument. | manuscript §15.1 | RESOLVED |
| R8 | Extend implementation-diverse checking beyond two dimensions. | The general proof and producer remain dimension-general for bounded rational polytopes, but the separate checker remains one-/two-dimensional. This is stated as an assurance boundary and a future project rather than implied completion. | manuscript §§4, 13 and 15; ASSURANCE | DELIBERATE_LIMITATION |
| R9 | An authenticated country application could strengthen practical significance. | No country verdict is manufactured from incomplete public terms. The paper gives a complete translation/audit protocol and preserves authenticated instruments and an actual declared rule as future empirical work. | manuscript §14 | DELIBERATE_LIMITATION |

## What the strengthening establishes

The added family is not a larger decorative example. It removes the three simplifications identified by the reviewer and yields a closed-form parameter boundary. With late reference uplift `lambda`, the duration cap is

`(750 - 10 lambda) / (15 + lambda)` for `0 <= lambda < 75`.

It crosses the programme-service cap of 25 exactly at `lambda = 75/7`. At the retained worked value `lambda = 20`, the oblique trigger reduces the robust early-payment ceiling to `110/7`. The argument is derived in the manuscript; the code reproduces it and independently reconstructs the trigger regions and scalar inequalities.

## Verification after revision

The final frozen package must pass normal and optimised replay, normal and optimised separate checking, normal and optimised regression tests, manifest verification, a fresh-extraction replay, document compilation and page-by-page inspection. The separate checker reports its precise counts and scope. These checks support the implementation and examples; the paper's universal results depend on their written proofs.

## Post-revision adversarial pass

A read-only max-effort `claude-opus-5` pass independently recomputed the headline rational results and found no mathematical error. It nevertheless identified four release-level defects, all corrected before freeze:

| Finding | Resolution | Public evidence |
|---|---|---|
| A dropped backslash rendered `qquad` in the nonproportional-family inequalities. | Corrected the TeX and regenerated the PDF, Markdown and HTML; raw-TeX PDF preflight and readable-scale page inspection pass. | manuscript §12.4; `results/document-qa.json`; `VISUAL_QA.md` |
| `SHA256SUMS.txt` still described version 2 during pre-freeze review. | Regenerated the manifest only after every public file was final; manifest replay is required both in place and after fresh extraction. | `SHA256SUMS.txt`; `code/check_manifest.py` |
| The draft web page quoted numerical counts from a private reviewer-audit file. | Removed the sentence. The public page now reports only checks reproducible from the deposited package. | Evidence Press release body; `ASSURANCE.md` |
| The declared uplift parameter and range were not both consumed by the verifier. | Split the declared uplift into a parameter and cash-flow shape; derive the cap coefficients and switch from them in the producer; independently reconstruct the family from direct cash-flow rows; add parameter and range mutations. | `data/contracts.json`; `code/verify.py`; `code/check_certificates.py`; `code/test_revision.py` |

The cross-model report is retained as private operational evidence, not as a theorem premise. Every load-bearing argument and executable input is distributed in the public package.

## Remaining assessment boundary

This revision makes the contribution more substantive and closes every required publication defect. It does not claim that an automated strengthening converts the supplied prospective 2-star assessment into a 3-star or 4-star result. Originality, significance and REF quality remain matters for independent scholarly judgement. No global priority, legal authentication, institutional adoption, welfare result or country-level verdict is asserted.
