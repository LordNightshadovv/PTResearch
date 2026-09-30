from .base import estimate
def progress(completed, total, samples=()): return estimate("parameter-sweep", completed, total, samples)
