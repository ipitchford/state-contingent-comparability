# State-contingent comparability — version 3.0

Research creator: **Anonymous**. Prepared for Evidence Press on **15 October 2026**. This is a self-contained research and reproducibility package: the paper states every definition, assumption, proof and scope qualification on which its claims depend. The private reviewer material is not required to understand, verify or reuse the result.

Public identity: DOI [`10.5281/zenodo.23392424`](https://doi.org/10.5281/zenodo.23392424); source repository [`ipitchford/state-contingent-comparability`](https://github.com/ipitchford/state-contingent-comparability). These identifiers refer to version 3.0.0 and do not enlarge its assurance status.

## Read

- [Full manuscript](state-contingent-comparability-v3.pdf): the scientific argument, proofs, exact examples, literature positioning and claim boundaries.
- [Accessible manuscript](manuscript.md) in Markdown and [HTML](manuscript.html).
- [Plain-language feature](editorial/Evidence_Press_feature.md), with [HTML](editorial/Evidence_Press_feature.html).
- [AI index](AI_INDEX.md): a file-by-file route through the claims and evidence.
- [Structured claims](CLAIMS.json), [sources](SOURCES.md), [assurance](ASSURANCE.md), [provenance](PROVENANCE.md), [licences](LICENSES.md) and [research gates](RESEARCH_GATES.json).
- [Repository CI](.github/workflows/verify.yml) replays the producer, independent checker, negative controls and manifest on supported Python versions.
- [Response to the supplied version-2 review](RESPONSE_TO_REVIEW.md), retained as traceability rather than as part of the proof.

## Main result and extension

For fixed old claims, positive discount factors and piecewise-affine new service, the declared three-coordinate comparability screen reduces on each reachable trigger region to two affine inequalities and one quadratic duration inequality. Exact facewise minimisation therefore supplies finite certificates for the bounded rational instances studied here.

The paper proves that componentwise smaller payments can still fail a duration veto, even after a perturbation makes both endpoint tests pass strictly. It also derives complete scalar payment intervals under partial information. A new nonproportional family has unmatched old payment profiles and an oblique trigger: the sharp implementable early-payment cap is `25` off-trigger and `110/7` on-trigger. As the late reference uplift `lambda` varies, duration replaces programme service as the binding constraint exactly at `lambda = 75/7`.

These are conditional mathematical results about declared cash flows and rules. They do not authenticate a contract, infer an institution's preferences, establish welfare or sustainability, or issue a country-level verdict.

## Reproduce

Python 3.10+ and the standard library suffice for all financial checks. From this directory run:

```sh
python3 -B code/verify.py
python3 -B -O code/verify.py
python3 -B code/check_certificates.py
python3 -B -O code/check_certificates.py
python3 -B code/test_revision.py
python3 -B -O code/test_revision.py
python3 -B code/check_manifest.py
```

`verify.py` reconstructs the frozen exact results. The separate checker does not import the producer or optimiser. It rebuilds 16 model domains and 10 trigger regions from `data/contracts.json`, checks 48 exact minima and 252 coefficient-determining identities, and verifies the two scalar intervals in the new oblique-trigger family. The regression suite includes a self-consistent shortened-domain certificate that the checker must reject.

The first six commands do not alter shipped outputs. `python3 -B code/verify.py --write` is a deliberate generator for a changed model; it changes the release identity and is not a verification command. `code/render_figures.py` regenerates scientific figures with NumPy and Matplotlib. The PDF is built by running `pdflatex` twice from the package root on `manuscript/paper.tex`.

The producer's exact quadratic kernel is dimension-general for bounded rational polytopes. The independently written checker covers the one- and two-dimensional certificates shipped here. That difference is an explicit assurance boundary, not an omitted dependency. No private review file, remote data service, proprietary package or unpublished script is needed for these checks.

## What changed from version 2

Version 3 closes the version-2 review's one publication-blocking defect: certificate domains and trigger regions are no longer trusted from the certificate itself. It also adds the strict endpoint perturbation, the nonproportional oblique-trigger family, clearer implementation boundaries, durable author/year labels in accessible formats, and a scientific manuscript free of review-history dependence. The strengthening improves the result without claiming an external review verdict or a particular REF rating.
