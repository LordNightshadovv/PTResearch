# Bounded workflow contract

This reference is the compact contract behind `pt-self-improvement`. A case ledger is a record of
what was observed and tested, not a replacement for the PT scientific contracts.

## Ledger fields

The JSON template has five layers:

| Layer | Required meaning |
| --- | --- |
| `source`, `budget` | provenance, authority boundary, maximum lineages/iterations/reviews, and an explicit exit condition |
| `splits` | development IDs and held-out manifest metadata; the held-out result is procedurally sealed |
| `rules` | one mechanism per lineage, hash-bound map/reduction evidence, implementation, review, numeric development screen, frozen candidate, held-out receipt, timeline, and promotion metadata |
| `events` | append-only status history for proposed, rejected, deferred, provisional, held-out evaluation, and promoted decisions |
| `pending_consolidation` | canonical-source discovery and a deferred patch when the writable AGENTS pair is unavailable |

The validator deliberately accepts a blank initialized ledger. It becomes stricter as a rule moves
from `proposed` to `provisional` or `promoted`. A promoted rule must pass every gate; omitted or
ambiguous evidence is a failure-closed condition.

Promoted rules reference real local artifacts with lowercase SHA-256 digests. The candidate receipt
binds an actual candidate payload hash to the frozen candidate; acceptance and held-out receipts
bind their identities, acceptance rule, evaluator role, times, and public numeric metrics. The
development screen computes capability-floor/tolerance and efficiency comparisons from the stored
numbers, while the held-out evaluator is checked against the frozen thresholds. A receipt file
hash authenticates the local file at validation time; it does not prove that an evaluator was
honest or that a physical result generalizes beyond the declared scope.

## Evidence ordering

Map records preserve trajectory-local observations. The reduction stores their IDs and a concise
receipt of the evidence that survived. The proposal, implementation, review, and development
screen may refer to development records only. The frozen candidate and acceptance rule are written
before held-out evaluation. The held-out record stores only sealed metadata, a digest, and an
independent pass/fail result; it does not store raw traces or repair advice.

The validator treats exact held-out trajectory IDs appearing outside the `held_out` record or the
top-level split declaration as a leak. This is a procedural check. It does not create a filesystem
or confidentiality boundary, and the ledger must say when an independent evaluator was not
available.

## Capability and efficiency

`development_screen.capability_floor.passed` must be true and
`development_screen.efficiency.improved` must be true for a candidate to proceed. The
`combined_regression_checks.passed` field covers existing workflow checks and the new mechanism's
own contract. A candidate that saves time by skipping evidence, verification, or required PT
artifacts fails the capability floor.

## Managed policy section

The promotion script uses exactly one marked section in each AGENTS file:

```text
<!-- BEGIN PT-SELF-IMPROVEMENT RULES (managed; preserve surrounding content) -->
...
<!-- END PT-SELF-IMPROVEMENT RULES -->
```

Entries are keyed by `PTSI-*` IDs. Existing entries are never silently overwritten: re-promoting
the same byte-equivalent entry is a no-op, while a conflicting entry requires a new ID and an
explicit supersession link. The section has a finite entry limit so policy cannot grow without
bound. Dual-policy and ledger writes use a recovery journal; a target-write failure rolls back all
changed targets or leaves a journal that names the incomplete recovery.
