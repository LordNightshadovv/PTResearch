FROM python:3.11-slim

RUN python -m pip install --no-cache-dir 'numpy==1.26.4' 'scipy==1.13.1'

WORKDIR /case
CMD ["python", "-c", "import numpy, scipy; print('NumPy', numpy.__version__, 'SciPy', scipy.__version__)"]
