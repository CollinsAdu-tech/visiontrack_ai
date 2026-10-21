# VisionTrack AI -- backend image
#
# opencv-python needs a couple of system libraries that python:3.11-slim
# doesn't ship (libGL, libglib) -- without them, `import cv2` fails at
# container startup, not at build time, which is a much more annoying
# place to discover it. Installed explicitly below.
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

# Writable at runtime for uploads/outputs/model weights -- not baked
# into the image (see docs/deployment.md for pre-baking weights).
RUN mkdir -p uploads outputs models

ENV UPLOAD_DIR=uploads \
    OUTPUT_DIR=outputs \
    PYTHONUNBUFFERED=1

EXPOSE 8000

# No `curl` in this slim image -- use Python's own stdlib for the
# healthcheck instead of adding a package just for this.
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health', timeout=3)" || exit 1

# Single worker by default: the in-memory ResultsStore (see
# app/services/results_store.py) is only correct with exactly one
# worker process -- see docs/deployment.md before raising --workers.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
