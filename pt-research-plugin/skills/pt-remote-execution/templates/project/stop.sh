#!/usr/bin/env sh
test -f run/runner.pid && kill -TERM "$(cat run/runner.pid)"
