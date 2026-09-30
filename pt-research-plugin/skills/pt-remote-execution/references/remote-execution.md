# Remote Linux execution

Keep integrations in the plugin only. Keys, passwords, tokens, installed solvers, container images, caches, and run results remain in user/project directories outside it. Use `/home/pt-runner/PT-Solvers`, `/home/pt-runner/PT-Simulations`, and `/home/pt-runner/.cache/pt-research` by default. `pt-runner` is non-root, has no default sudo or ordinary docker-group membership; prefer rootless Podman/Docker, Apptainer on clusters, then native installs.

`pt_remote.py` validates alias/project identifiers, invokes `ssh -- alias command` using argument arrays, prefers rsync, uses safe project manifests and checksum verification, and never overwrites a run unless explicitly requested. Its bootstrap is plan-only. Doctor/probe are read-only. `clean` is dry-run by default, rejects containment failures, preserves the newest checkpoint, and requires an explicit confirmation flag to remove eligible generated files.

Persistent runs prefer `systemd --user`, then `systemd-run --user`, scheduler, then documented `setsid`/`nohup`. A run owns `job.json`, logs, checkpoint directory, `status.json`, and progress history. `fetch-results` retrieves only declared results/logs/checkpoints/manifests, verifies checksums, creates a local receipt, and never removes the remote copy. A generated macOS LaunchAgent is not installed automatically and stops after a terminal state.
