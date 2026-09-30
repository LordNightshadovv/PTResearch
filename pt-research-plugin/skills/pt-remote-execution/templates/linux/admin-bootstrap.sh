#!/usr/bin/env sh
# PLAN ONLY. An administrator reviews and runs this deliberately.
set -eu
id pt-runner >/dev/null 2>&1 || useradd -m -s /bin/bash pt-runner
install -d -o pt-runner -g pt-runner -m 0750 /home/pt-runner/PT-Solvers /home/pt-runner/PT-Simulations /home/pt-runner/.cache/pt-research
# Do not add pt-runner to sudo or the ordinary docker group.
