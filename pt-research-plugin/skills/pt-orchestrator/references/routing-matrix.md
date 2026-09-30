# Physics-first routing matrix

| Governing physics | Preferred route | OpenFOAM role |
|---|---|---|
| Diffraction, pupil/image formation, Fourier propagation | `wave_or_fourier_optics` | Reject as principal route |
| Low-dimensional oscillators and modal reductions | `ode_or_reduced_order_mechanics` | Usually unnecessary |
| Discrete rigid bodies, impacts, frictional contact | `rigid_body_and_contact` | Reject unless coupled fluid fields dominate |
| Solid stress, deformation, eigenmodes | `solid_mechanics_fem` | Only if installed solid formulation matches |
| Piezoelectric/electromechanical coupling | `specialized_multiphysics_fem` | Partial downstream acoustics only when justified |
| Continuum momentum, pressure, free surfaces, heat/species transport | `openfoam_continuum` | Candidate after capability/version gate |
| Multiple strongly coupled domains | `hybrid_multi_solver` | One component with explicit interfaces |
| Unsupported equations with deterministic discretization | `custom_numerical_code` | Use only if OpenFOAM is not a better fit |
| Analytic model already answers the prompt | `no_simulation_recommended` | None |

Route from governing equations, fields, boundary conditions, coupling, and requested observables—not object names or familiar software.
