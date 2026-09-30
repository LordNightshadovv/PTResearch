# Candidate decision rules

## Hard gates

Filter a candidate as a final whole-chain model when any unresolved condition applies:

- it does not connect controlled input to a prompt-relevant observable;
- it is a component presented as complete;
- its regime contradicts the apparatus;
- its essential parameters cannot be measured or estimated and sensitivity analysis is impossible;
- it has no falsifiable or discriminating prediction;
- central equations or applicability cannot be verified;
- it duplicates another candidate without a distinct mechanism or regime;
- a magnitude/timescale check shows it is too weak;
- it is a solver or numerical method rather than a physical model.

Retain a filtered candidate as a component, correction, limiting case, control hypothesis, or unresolved alternative when appropriate.

## Advisory score

| Criterion | Weight |
|---|---:|
| Prompt relevance | 20 |
| Full causal-chain coverage | 20 |
| Evidence quality/directness | 15 |
| Mathematical completeness | 15 |
| Falsifiability/distinctive predictions | 10 |
| Parameter measurability | 10 |
| Regime fit | 5 |
| Analytical/numerical tractability | 5 |

Give a normalized sub-score and short explanation for every dimension. Use the total as a transparent aid, not an automatic ranking.

## Filtered-candidate ledger fields

For every filtered candidate record:

1. exact name or descriptive name;
2. search/source where it entered;
3. causal links covered;
4. why it seemed plausible;
5. exact filter reason and hard gate, if any;
6. evidence supporting the decision;
7. residual use;
8. evidence that would trigger reconsideration.

## Selection outcomes

- `single_sufficient_working_model`: one verified candidate covers the chain at useful fidelity.
- `coupled_model_stack`: compatible components jointly cover the chain.
- `competing_whole_chain_models`: multiple complete hypotheses remain discriminable but unresolved.
- `insufficient_evidence_to_select`: central links or provenance remain too weak.

Prefer one to three recommendations. Retain a simple baseline when it supplies scaling or a limiting case. Keep alternatives that make distinct predictions. Do not force a winner through scoring.

## Multiple objectives

Preserve each prompt-defined objective. Identify dominance and tradeoffs across parameter regimes. Report a Pareto frontier when no unique optimum follows. Scalarize only when the prompt/user supplies preferences or a clearly stated physical convention is defensible. Keep optional real-world metrics separate.
