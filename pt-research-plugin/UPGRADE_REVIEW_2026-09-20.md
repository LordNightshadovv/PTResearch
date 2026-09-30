# PT Research plugin upgrade review — 2026-09-20

This audit covers the scientific workflow, calibration/validation boundary, evidence provenance,
truthful stage claims, and the recursive process-learning handoff in the PT Research plugin. It
does not claim that a solver ran or that the workflow empirically improved. The preserved
`upstream-original/` snapshots were read for context and were not edited.

## Evidence and scope

The review used the workspace plugin at `/Users/vold/Documents/PTResearch/pt-research-plugin`, its
first-party and bridge `SKILL.md` files, the v3 contract and state machine, the calibration
contract added during this upgrade, and the self-improvement helper. The baseline software suite
was run before these documentation changes:

```text
python3 -m unittest discover -s tests -v
Ran 80 tests in 17.009s
OK
```

The complete baseline output is retained at
`/private/tmp/pt-plugin-upgrade-20260920-baseline-unittest.txt`. A full-tree baseline copy of the
pre-change plugin is retained at
`/private/tmp/pt-plugin-upgrade-20260920/pt-research-plugin/`.

The review uses the process boundary described by [SoL-Pi](https://nvlabs.github.io/SoL-Pi/):
bounded opportunities, evidence-preserving reduction, frozen acceptance, independent held-out
evaluation, and capability floors. Those process results are not evidence about this plugin's
scientific accuracy. The distinction between numerical verification and physical validation follows
the [NASA validation assessment overview](https://www.grc.nasa.gov/www/wind/valid/tutorial/overview.html)
and [validation-assessment guidance](https://www.grc.nasa.gov/www/wind/valid/tutorial/valassess).
Data and artifact provenance requirements are informed by [NIST SP 1500-18r2](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/1500-18/NIST.SP.1500-18r2.html).

## Prioritized findings

### P0 — stage strings were not sufficient evidence of physical validation

The previous state-machine row for `physically_validated` required only “reference comparison”
and a physical-validation report. It did not name a held-out split, uncertainty treatment,
predeclared criterion, calibration boundary, or a binding between the report and the frozen model.

This was reproduced without touching a real case. A disposable copy of the valid
`01-pinhole-sunglasses` fixture was changed from `synthetic_smoke_tested` to
`physically_validated`, and its claim was changed to completed while the handoff still contained
only `highest_state: runnable_synthetic` and no physical-validation report. The existing
`scripts/validate_artifacts.py` returned exit 0. This demonstrates an observed stage/claim
consistency gap; it does not demonstrate that every malformed v3 case passes every contract.
The reproduction is retained at
`/private/tmp/pt-plugin-upgrade-20260920/bogus-physically-validated/` with its validator output.

The updated state machine now requires, for `physically_validated`, a version-1 calibration plan
with `status: physically_validated`, disjoint fit/validation IDs and hashes,
`independent_validation.status: passed`, a frozen-fit binding or frozen model/configuration and
input binding when no parameter is fitted, an uncertainty-aware acceptance criterion, and a passed
independent `physical_validation` report. It also requires cross-artifact consistency before a
transition.

### P0 — calibration, fitting, and physical validation needed an explicit contract boundary

Earlier documentation required “uncertainty” and “compare with experiment” but did not prescribe
the artifact binding needed to distinguish a fitted parameter from independent validation. The
updated theory reference, v3 contract, state machine, and README require
`calibration_plan.yaml` with `calibration_contract_version: 1` for advanced calibration or physical
claims. New scaffolds remain `planned` with claim ceiling
`no_calibration_or_physical_validation_claim`; `not_required` needs justification and cannot carry
fitted roles. A calibrated claim needs a frozen fit artifact and fit residual; physical validation
also needs held-out observations, data hash, a binding to the frozen fit or, when no parameter is
fitted, the frozen model/configuration and inputs, uncertainty-aware comparison, and a passed
physical-validation report. Legacy cases remain at their prior ceiling until explicit migration or
opt-in.

### P1 — uncertainty and validation coverage were named but not operationally reviewable

The prior instructions often requested sensitivity or uncertainty without requiring a decomposed
error budget or a coverage view. The new
`skills/pt-theoretical-research/references/validation-and-reproducibility.md` defines separate
measurement/repeatability, calibration, numerical/discretization, model-form, and
sampling/coverage contributions, their units and propagation assumptions, and an
observable × regime × apparatus-branch × parameter-range coverage matrix. It requires failed and
uncovered rows to remain visible and prevents a nearby successful run from promoting an untested
branch.

### P1 — acceptance rules could be changed after results were seen

The scientific workflow now requires a predeclared metric/formula, direction, units, threshold,
uncertainty method, falsifier, failure condition, split, input/software hashes, and evaluator
before fitting, execution, or comparison. A changed criterion is a new plan/version and cannot
rescue an earlier failure. The bridge instructions carry this requirement into CFD code changes,
experiments, Foam-Agent generation, mesh/time-step gates, and report rendering.

### P1 — provenance needed to bind claims to bytes and commands

The revised instructions require source/artifact locators, content hashes, exact commands,
environment and solver revision, input/output hashes, timestamps, warnings, failures, and metric
calculation provenance. They explicitly classify self-declared booleans, plausible hash strings,
file presence, and solver exit codes as advisory evidence unless bound to receipts.

The learning implementation now closes that specific boundary. Promoted rules require local
SHA-256-checked candidate, acceptance, and held-out receipt artifacts; receipt identities and
candidate digests are cross-bound to the frozen rule; capability and efficiency results are
recomputed from frozen numeric thresholds; held-out evaluation is sealed and feedback-free; and
policy/ledger writes have an atomic rollback journal. Malformed or tampered evidence therefore
fails validation rather than becoming a promotion. The focused tests exercise these bindings and
rollback paths. They still establish implementation invariants only: no experiment or independent
workflow evaluation was run, so the plugin must not claim empirical recursive improvement from
these tests.

### P2 — installed plugin source was stale and differed from the workspace

`read_marketplace_name.py` returned `personal`, and the personal marketplace entry points to the
local source `./plugins/pt-research-plugin`. `codex plugin list` resolved that entry to
`/Users/vold/plugins/pt-research-plugin`, installed/enabled at
`0.5.0+codex.20260726031254`. The workspace source is
`/Users/vold/Documents/PTResearch/pt-research-plugin` at base version `0.7.0`; the two directories
are ordinary, non-symlinked directories with different manifests and skill hashes. No cache,
marketplace, or installed source was edited during this audit. After review, the safe update path
is a reviewed overlay to the registered local source, the Plugin Creator cachebuster helper, and
`codex plugin add pt-research-plugin@personal`; no manual marketplace edit or destructive sync.

### P2 — documentation overstated the supported Python range

The README said Python 3.9+, while the dependency policy declares Python 3.10+ for plugin scripts.
The baseline suite was observed passing under Python 3.9.6, but that runtime is outside the
supported policy. The README now reports the policy minimum and the observed test runtime without
claiming that 3.9 is unsupported by every source file.

## Changes made in this audit

- `skills/pt-theoretical-research/SKILL.md` now requires explicit falsifiers and rejection
  thresholds for serious candidates, pre-registered acceptance, calibration/held-out boundaries,
  decomposed uncertainty, coverage status, and bound reproducibility evidence.
- `skills/pt-theoretical-research/references/validation-and-reproducibility.md` adds the reusable
  operational contract for acceptance, calibration, uncertainty/error budgets, coverage, evidence
  provenance, partial outcomes, and review order.
- `skills/pt-orchestrator/references/scientific-contract-v3.md` adds pre-registered acceptance,
  calibration v1, held-out physical validation, coverage, error-budget, provenance, and
  cross-artifact claim-consistency gates.
- `skills/pt-orchestrator/references/state-machine.md` names the required evidence for numerical
  and physical transitions, blocks contradictory late-stage strings, and defines truthful partial
  outcomes.
- `skills/pt-report-renderer/SKILL.md`, `skills/pt-openfoam-environment-manager/SKILL.md`, and
  `skills/pt-remote-execution/SKILL.md` carry the same claim and receipt boundaries into reports,
  runtime probes, and remote execution.
- All eight non-original upstream bridge `SKILL.md` files now preserve acceptance criteria,
  uncertainty/provenance, failed outcomes, and orchestrator-only stage advancement at their
  relevant boundary. The preserved `upstream-original/` files are unchanged.
- `README.md` documents the scientific acceptance lane, the calibration plan and partial claim
  ceiling, the verified local-plugin update flow, Python 3.10+, and the limit of static tests.
- `scripts/validate_plugin.py` now treats `calibration-plan.schema.json` as a required shared
  schema, so the new calibration contract cannot silently disappear from a structurally valid
  release.

## Verification boundary

The baseline 80-test suite passed before the edits. In the frozen shared workspace, the post-change
suite passed with 112 tests in 6.653 seconds under the available `python3` runtime; the captured
output is `/private/tmp/pt-plugin-upgrade-20260920-release-unittest.txt`. The PT plugin validator
passed. All 16 top-level skill directories passed `quick_validate.py` using the available
Anaconda Python runtime (the system Python did not have PyYAML, so it could not run those YAML-based
validators). The disposable bogus physical-claim case now fails with exit 1 because it lacks the
version-1 calibration plan and numerical verification report. A valid synthetic fixture passes
inspection-only `--allow-partial` with `package_status=runnable_synthetic` and exit 0. The generic
Plugin Creator validator passes after the self-improvement agent metadata was corrected to the
supported `policy` and `interface` fields.

After adding the required calibration schema check, the focused plugin-structure and calibration
checks passed with 24 tests in 0.416 seconds. The full 112-test result above predates this
one-line validator coverage addition; the addition is structural and was covered by the focused
checks.

The calibration validator checks declared metadata, local frozen JSON/evidence bytes, hashes,
timestamps, split identities, and cross-artifact consistency. It does not hash or reread external
raw measurement data, derive residuals from raw observations, rerun an optimizer or solver, or
establish physical truth. No scientific experiment, solver run, calibration fit, or independent
recursive workflow evaluation was performed here. Documentation and static tests can improve the
contract and expose fail-before behavior; they cannot establish physical validity or empirical
recursive improvement.
