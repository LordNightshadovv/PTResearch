FROM python:3.11-slim
RUN pip install --no-cache-dir hcipy==0.7.0
CMD ["python", "-c", "import hcipy; print(hcipy.__version__)"]
