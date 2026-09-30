from .base import estimate
def progress(current, target, samples=()): return estimate("iterations", current, target, samples)
