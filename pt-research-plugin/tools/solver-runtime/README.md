# Solver runtime layer

This directory contains version locks, official-source installer generation, platform detection, smoke-test requirements, templates, validation cases, container recipes, and package launchers for the six numerical runtimes selectable by `pt-simulation-router`.

It intentionally contains no solver binary or third-party container image. `solver_runtime.py install` can only act after the user has authorised execution on the current computer. `solver_runtime.py package` creates an installer for another computer and refuses to describe the package as a runnable scientific case: a matching, passed platform-test receipt proves only the locked runtime. A route-specific executable package and its synthetic receipt are required before `runnable_synthetic`.
