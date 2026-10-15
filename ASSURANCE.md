# Assurance and claim boundary

**Object assessed:** version 3.0.0, dated 15 October 2026. The manuscript itself supplies all definitions, assumptions, derivations and limitations needed to assess the scientific claims. Neither the private audit nor this assurance note is load-bearing evidence for a theorem.

## What is checked

- Written proofs establish the universal mathematical statements under fixed old claims, positive discount factors, positive denominators, nonnegative service, bounded domains and the declared information order.
- The producer reconstructs the frozen exact financial results from `data/contracts.json` and binds its data and calculation files in `input-lock.json`.
- A separately written checker imports neither the producer nor the optimiser. It rebuilds 16 domains and 10 trigger regions from the declared model, verifies equality ownership and reachability, recomputes 48 exact minima and 252 coefficient-determining identities, and reconstructs both scalar intervals in the new family.
- Normal and optimised Python runs agree. Regression checks cover 200 payment-removal identities, 100 general payment models and 4,100 direct comparisons, including positive-floor cases and an exact strict-endpoint perturbation.
- Negative controls include a false minimum, a million-unit data mutation and a self-consistent shortened-domain certificate. All are rejected for the intended reason.
- The nonproportional family consumes its declared uplift parameter, half-open parameter range and year-6 uplift shape. The producer derives the duration-cap coefficients and binding switch from those fields; the separate checker reconstructs them from direct cash-flow rows. Mutating the parameter changes the result, while excluding it from the declared range fails explicitly.

## What the evidence means

The two implementations provide useful implementation diversity, not independent external reproduction: they were produced in the same AI-assisted revision process. Finite replay checks the declared examples and implementation; it does not prove the paper's universal theorems, bibliographic completeness or real-world applicability. The universal results rely on the written arguments in the manuscript.

The supplied automated audit assessed version 2. It found the mathematics sound but identified that the old separate checker trusted a certificate-supplied domain. Version 3 repairs that defect and adds a direct negative control. It also addresses the recommended strict endpoint perturbation and adds a nonproportional oblique-trigger family whose binding constraint genuinely changes. The current author-side checks confirm those changes; no independent human peer review or official REF assessment is claimed.

A read-only max-effort adversarial pass by `claude-opus-5` then recomputed the headline rational results and found no mathematical error. It identified a rendered-TeX defect, a stale pre-freeze manifest, one public sentence derived from a non-distributed reviewer audit, and an unconsumed parameter-range declaration. Those defects were corrected before the release archive was frozen. This cross-model pass is author-coordinated review, not independent human peer review, and no public theorem depends on its report.

## Boundaries

The executable model uses rational data and integer payment dates. The mathematical statements allow any fixed positive rational discount factors at finitely many dates. The producer's quadratic kernel is dimension-general for bounded rational polytopes; the independent checker is deliberately limited to the shipped one- and two-dimensional cases.

The package does not authenticate legal text, recover undisclosed payment terms, infer institutional preferences, establish debt sustainability, value instruments at market prices, determine welfare, or contradict a documented country decision. The Paris Club's flexible institutional judgement is not equated with the paper's separate-veto screen.

The literature search is documented and substantial but not exhaustive. Exact-example priority remains unresolved. `input-lock.json` detects drift relative to the frozen release bytes; it is not a digital signature and does not protect against coordinated replacement of both data and trust records.
