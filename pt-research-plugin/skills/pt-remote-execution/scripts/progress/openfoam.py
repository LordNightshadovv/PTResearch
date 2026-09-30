from .base import estimate
def progress(current_time, start_time, end_time, samples=()): return estimate("simulation-time", current_time - start_time, end_time - start_time, samples)
