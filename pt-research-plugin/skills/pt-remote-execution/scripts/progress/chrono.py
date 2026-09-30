from .base import estimate
def progress(current, target, samples=()): return estimate("simulation-time", current, target, samples)
