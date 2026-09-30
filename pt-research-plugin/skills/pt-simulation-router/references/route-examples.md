# Routing examples

- Pinhole sunglasses: `wave_or_fourier_optics`; reject OpenFOAM because the dominant equations are aperture propagation and image formation.
- Singing capacitor: normally `specialized_multiphysics_fem` or `hybrid_multi_solver`; stock OpenFOAM cannot silently replace electromechanical strain and solid modes.
- Air vortex with a water-air core: `openfoam_continuum` only after mapping transient incompressible multiphase flow, gravity, surface tension, rotational forcing, interface resolution, conservation, mesh, and time-step requirements.
