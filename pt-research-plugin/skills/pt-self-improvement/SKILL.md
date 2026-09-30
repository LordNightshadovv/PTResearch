---
name: pt-self-improvement
description: Run bounded, evidence-preserving process-learning loops for PT research work, keeping development evidence separate from sealed held-out evaluation and promoting only transferable workflow rules into the project policies.
---

# PT self-improvement

Use this skill to improve the PT research workflow itself. It changes scoped instructions,
templates, or routing records; it does not change model weights, provider behavior, the Codex
harness, solver physics, or a user's authority. The loop is a disposable research artifact for a
case or bounded project episode. Do not grow a permanent coordinator or launch open-ended search.

## Load policy and locate the writable source

Before reading a case or proposing a rule, explicitly load both policy files:

1. Read the workspace `AGENTS.md` from the project root.
2. Read the PT plugin `AGENTS.md` from the writable plugin source selected for this task. Plugin
   discovery is a filesystem task: resolve the plugin path from the active project or installation
   metadata, then verify it is writable and is not an immutable marketplace/cache copy. Never
   assume the current working directory is the canonical source, and never edit an installed
   cache merely because it contains a matching skill.
3. Read this skill's [workflow](references/workflow.md), [SoL-Pi adaptation](references/sol-pi-adaptation.md),
   and the [ledger template](templates/audit-ledger.json).

If the canonical writable plugin source cannot be identified, record a `deferred` consolidation
event with the discovered paths and the reason. Keep a pending patch in the active project ledger;
do not silently redirect the rule to a cache. A process lesson may still be used provisionally in
the current case, but it is not promoted into AGENTS files until the canonical pair is writable.

## Safe default and bounded authority

Learning is enabled by default for the current authorized PT project, but only for reversible,
readable process improvements. It may inspect existing case trajectories, receipts, failures,
review notes, and validation output already in scope. It may update the case ledger and a proposed
rule. It may not broaden filesystem, network, solver-installation, execution, outreach, or data
access authority. Existing PT artifact gates still govern simulation setup, installation, costly
sweeps, remote work, and publication.

Every case keeps one ledger at `runs/<case-id>/learning/audit-ledger.json`. Initialize it from
the template and validate it with:

```bash
python3 skills/pt-self-improvement/scripts/self_improvement.py init \
  --case-dir /absolute/project/runs/<case-id> --case-id <case-id>
python3 skills/pt-self-improvement/scripts/self_improvement.py validate \
  --ledger /absolute/project/runs/<case-id>/learning/audit-ledger.json
```

The initializer refuses to overwrite an existing ledger. Ledger writes are append-oriented and
must retain prior proposed, rejected, deferred, provisional, and promoted rules. A rejected rule
is useful negative evidence; do not delete it to make a later promotion look cleaner.

## One bounded lineage at a time

Each candidate rule gets a unique `rule_id`, exactly one `lineage_id`, and exactly one
`mechanism_id`. A lineage may not quietly combine prompt, routing, memory, tool, and evaluation
changes. If several independent ideas are worth testing, create separate lineages and cap their
count in the ledger.

Use the following order for each selected lineage:

1. **Opportunity analysis.** Mine actual in-scope trajectories or receipts for an avoidable,
   repeated decision or failure. Record the observation, locator, and proposed opportunity before
   spending implementation budget. A plausible idea without trajectory evidence remains proposed.
2. **Map.** Have independent map records inspect trajectories separately. Each map record names
   its source trajectory, the observed boundary, the avoidable work, and the evidence locator.
   Map records are raw observations; do not let a reducer silently rewrite them.
3. **Evidence-preserving reduce.** A reducer combines only mapped record IDs and records what
   evidence was retained, what was contradictory, and why the opportunity is actionable. A short
   receipt is valid only when its cited lines or artifact hashes can be checked against the
   archived source. The reduction must finish before a proposal is accepted.
4. **Proposal and implementation.** State one mechanism, its expected capability and efficiency
   effect, its non-goals, and an explicit exit condition. Use a fresh disposable loop copy for the
   episode. The loop stops when the exit condition passes, the iteration/review budget is spent,
   evidence becomes invalid, or the candidate is rejected. Do not keep adding branches to a
   long-lived orchestrator.
5. **Independent review.** The implementer cannot be the reviewer. The reviewer checks the
   behavioral contract, scope, evidence links, and failure behavior. A failed review returns only
   to this lineage while budget remains; it does not change another lineage.
6. **Development screen.** Evaluate the candidate against a declared baseline on development
   inputs. Every capability metric must stay above its declared floor and at least one declared
   efficiency metric must improve. Run combined regression checks for the existing workflow as
   well as the new mechanism. Passing efficiency alone is never sufficient.
7. **Freeze, then held-out evaluation.** Freeze the candidate, acceptance rule, input manifest,
   and hashes before an independent evaluator sees held-out inputs. Keep the held-out set and raw
   results outside the development ledger and AGENTS files. A held-out result may be represented
   by a digest and pass/fail receipt, but its task IDs, raw traces, and repair hints must not enter
   proposal, map, reduce, implementation, or review records. A failed held-out evaluation rejects
   the frozen candidate; it is not feedback for repair or another search episode in the same
   lineage. Directory names and hashes are bookkeeping, not a confidentiality or access-control
   boundary: isolation is procedural unless an independent evaluator provides a real boundary.

Without a fresh isolated evaluator and sealed held-out inputs, a development pass remains
`provisional`. It may inform the current case, but it cannot be promoted as transferable evidence.
Physical validation is a separate scientific activity: new measured data may revise a physical
model under the PT orchestrator's normal evidence gates, but those data must not be confused with
the held-out evaluation split used to judge a frozen workflow rule.

## Audit, promotion, and rollback

Record every meaningful state transition in `events`, including proposed, rejected, deferred,
provisional, held-out-evaluated, and promoted outcomes. If no meaningful opportunity exists at a
stage close, record the check and its no-op reason rather than inventing a lesson. A rule can be
`promoted` only when its ledger contains:

- map records and a distinct evidence-preserving reduction;
- a bounded implementation with an explicit exit condition and an independent reviewer;
- capability-floor, efficiency, and combined-regression evidence;
- frozen candidate and acceptance artifacts;
- an independently produced sealed held-out result with no feedback to the search lineage; and
- provenance, scope, validation limits, rollback instructions, and supersession information.

The candidate, acceptance, and held-out receipts must reference real local files by SHA-256. The
candidate receipt also hashes the candidate payload and matches the frozen candidate digest. Numeric
capability/efficiency comparisons and frozen held-out thresholds must compute to pass; a truthful
`passed: false` record remains a rejection. Receipt hashes authenticate local bytes at validation
time but do not establish evaluator honesty, access confidentiality, or scientific generalization.

Run the promotion helper only after validation:

```bash
python3 skills/pt-self-improvement/scripts/self_improvement.py promote \
  --ledger /absolute/project/runs/<case-id>/learning/audit-ledger.json \
  --rule-id PTSI-R001 \
  --plugin-agents /absolute/plugin/AGENTS.md \
  --workspace-agents /absolute/project/AGENTS.md
```

The helper updates one bounded, marked section in both AGENTS files, preserves surrounding user
content, refuses duplicate or conflicting rule IDs, and is idempotent. It never copies held-out
raw results into policy. A three-target recovery journal covers both policy files and the ledger;
if any write fails, the helper rolls back changed targets or leaves the journal for explicit
recovery. A superseding rule receives a new ID and points to the old one; rollback removes or
disables the old managed entry according to its recorded instruction. If either canonical AGENTS
file is unavailable, leave the ledger `deferred`/`provisional` and report the pending consolidation
path.

The initial protocol in the managed sections is an adopted project policy, not evidence that the
workflow has improved. Only later independently evaluated, transferable rules may claim empirical
promotion. At project handoff, consolidate eligible rules once, then report the ledger path,
promoted IDs, pending rules, held-out availability, and the highest claim ceiling. Do not claim
generalization from a hash, a unit test, or a single development trajectory.
