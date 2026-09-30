# LaTeX theoretical-model report contract

Write `reports/theoretical-model.tex` as a self-contained scientific-paper theoretical-model section. Use a real LaTeX document with numbered `equation` environments, a complete symbol table, inline citations, and a bibliography source. Compile it to `reports/theoretical-model.pdf` only after the content gates pass.

Required sections: problem/question; observables and variables; physical phenomenon and causal mechanism; model choice and literature foundation; assumptions/regime; governing equations and term-by-term physical meaning; derivation/model construction; main falsifiable prediction `Y=f(X;p)` with fixed-variable trends; limiting cases and dimensional checks; calculated example/table/plot; theory-to-solver mapping; validation/limitations/competing models; references.

For every equation, use the six machine-readable provenance classes, define
symbols/units/status/source, and explain origin, apparatus applicability, every term/sign,
dimensions, roles, competing balances, limits, assumptions, and falsifier. Put the exact
source locator and adaptation summary next to the equation when retrievable; otherwise state the
locator search and support limit. Do not create a generic equation catalogue or substitute solver
names for physical explanation.

The report must remain understandable without YAML, registries, source code, or other internal artifacts. Cite reliable sources beside claims, equations, constants, and models. Use a real calculated example, prediction table, or plot; do not label a plan as a completed prediction.

Reject `F(V)` and similar functions unless they are explicitly defined through constitutive,
geometric, or measured relations. Reject
`Y/Y_0=F(X/X_0;p/p_0)` as a principal result. Generate every example row from a displayed
prompt-specific equation and cite that equation in the caption or surrounding text.
