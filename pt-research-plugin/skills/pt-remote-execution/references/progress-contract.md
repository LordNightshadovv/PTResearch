# Status and progress contract

`status.json` is atomically replaced and has schema version 1. States are `preparing`, `queued`, `starting`, `running`, `checkpointing`, `paused`, `completed`, `failed`, `cancelled`, `stale`, `unreachable`, and `unknown`. It records project/run identifiers, solver/version, progress mode and units, elapsed seconds, optional percent/ETA/confidence, checkpoint, activity/update timestamps, warnings, and fatal error.

OpenFOAM uses simulated time over configured start/end time; Chrono uses simulated time, frames, or sweep cases; HCIPy must emit structured sweep/evaluation events; Elmer uses known time/frequency/load cases only; YADE uses target iteration/time/cases; generic sweeps use completed/total cases. Unknown denominators use `indeterminate` with null percent and ETA. ETA needs at least five recent positive samples and uses a robust rolling rate; it is an estimated remaining time, never a guarantee.
