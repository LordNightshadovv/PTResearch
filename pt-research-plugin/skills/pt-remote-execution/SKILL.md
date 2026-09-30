---
name: pt-remote-execution
description: Prepare, operate, and monitor an orchestrator-approved PT simulation on a dedicated Linux host through ordinary OpenSSH host aliases without handling secrets or granting unrestricted privilege.
---

# PT Remote Execution

Use only through `pt-orchestrator`, after an accepted single-solver route, simulation specification, target-platform decision, and explicit user choice of remote execution. Read [remote execution](references/remote-execution.md), [SSH security](references/ssh-security.md), and [progress contract](references/progress-contract.md).

Collect or reuse: host alias, remote username, LAN or approved mesh-VPN mode, project directory, locked solver, rootless/Apptainer/native policy, CPU architecture, GPU/backend, expected duration, report cadence, notification method, and local result destination. Never ask for or accept a password, key contents, key passphrase, Tailscale key, or OpenAI token.

Run `scripts/pt_remote.py doctor --host <alias>` and `probe` read-only first. Treat a changed host key as BLOCKED; do not use `StrictHostKeyChecking no`. `bootstrap-plan` only renders instructions. Administrator bootstrap, SSH-key creation, public-key installation, solver installation, LaunchAgent installation, firewall/VPN changes, and cleanup outside the project require explicit user approval.

Use a host alias, macOS ssh-agent/Keychain, argument arrays, and quoted remote paths. Do not keep a foreground shell open: start uses a user-owned persistent service/runner and must verify process/service, initialized solver state, writable log, atomic `status.json`, and no immediate fatal error. A successful command return alone never proves a simulation runs.

For status, logs, checkpoints, and notification rendering, make no changes. Schedule repeat checks only after one manual status read succeeds; stop checks for completed, failed, cancelled, or unreachable jobs. Report percentage and estimated remaining time only when the solver adapter has a defensible denominator and enough samples. Return remote receipts to the orchestrator with exact command, environment/version, input/output hashes, timestamps, warnings, failures, and coverage status; solver execution, convergence, calibration, and scientific acceptance remain separate gates. A remote receipt cannot advance `numerically_validated` or `physically_validated` without the corresponding predeclared criterion and validation artifacts.
