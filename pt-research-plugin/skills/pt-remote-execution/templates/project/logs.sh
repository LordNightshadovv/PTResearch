#!/usr/bin/env sh
tail -n "${1:-100}" run/stdout.log
