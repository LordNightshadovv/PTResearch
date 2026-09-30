# SoL-Pi adaptation boundary

Source: [SoL-Pi: Scaling Auto-Research Loops for Efficient Agent Harnesses](https://nvlabs.github.io/SoL-Pi/).
The article describes a scalable harness research pipeline rather than a PT scientific method.
This plugin adopts only the process ideas that can be represented as auditable instructions and
case artifacts.

## Adapted ideas

- **Opportunity analysis from actual trajectories.** SoL-Pi starts with an oracle analysis of
  observed trajectories before spending rollout budget. PT uses existing case traces, receipts,
  and validation failures to justify a process opportunity; it does not invent a benchmark gap
  from a prompt alone.
- **Map then evidence-preserving reduce.** SoL-Pi maps individual trajectories independently and
  reduces their evidence before proposing a mechanism. PT keeps trajectory-local map records and
  reducer references to archived lines or artifacts so a fluent summary cannot outrun its source.
- **One mechanism per lineage.** The article sends each direction through an independent loop.
  PT assigns one mechanism ID to one lineage and keeps unrelated prompt, routing, tool, and
  evaluation changes separate.
- **Bounded iterative implementation and independent review.** The article uses an explicit
  Ralph-style implementation loop and a different reviewer. PT records an exit condition,
  iteration/review caps, implementer, reviewer, and review evidence.
- **Development screen and sealed held-out evaluation.** SoL-Pi freezes the candidate and
  acceptance rule, evaluates held-out data separately, and does not feed held-out results back
  into the search. PT stores only a held-out digest and independent outcome in the development
  ledger; failure rejects the frozen rule rather than opening a repair episode.
- **Capability floor plus efficiency.** The article requires capability metrics to stay within a
  declared tolerance and at least one efficiency metric to improve. PT adds combined regression
  checks so a local process saving cannot remove scientific evidence or artifact gates.
- **Disposable skill loops.** The article favors a minimal reusable loop template over a growing
  permanent coordinator. PT instantiates a bounded case loop from templates, records its result,
  and discards loop-specific orchestration state at close.

## Boundaries and non-claims

This plugin cannot change model weights, provider pricing, Codex harness internals, or access
controls. A folder name or a hash does not isolate a held-out set; isolation is procedural unless
an independent evaluator and an actual access boundary provide more. A development pass without a
fresh sealed evaluator is `provisional`, not a transferable improvement. PT physical validation
may use new measurements to revise a physical model under the scientific evidence gates, but those
measurements are not held-out workflow evaluation feedback.

The article's reported harness scores and savings are not evidence about this plugin. A local unit
test proves an invariant of the ledger helper only. Empirical promotion requires new, independent
PT process evidence recorded in the ledger with its provenance and limits.
