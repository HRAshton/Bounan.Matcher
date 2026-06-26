FROM nvidia/cuda:12.9.2-cudnn-devel-ubuntu24.04

ARG DEBIAN_FRONTEND=noninteractive

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PATH="/opt/venv/bin:${PATH}"

RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates \
        ffmpeg \
        python3.12 \
        python3-venv \
        python3-pip \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m venv /opt/venv \
    && /opt/venv/bin/pip install --no-cache-dir --upgrade pip \
    && /opt/venv/bin/pip install --no-cache-dir cupy-cuda12x

COPY Matcher/requirements.txt /app/Matcher/requirements.txt
RUN /opt/venv/bin/pip install --no-cache-dir -r /app/Matcher/requirements.txt

WORKDIR /app

COPY Common /app/Common
COPY Matcher /app/Matcher
COPY runner.py /app/runner.py

RUN useradd -m -d /home/worker -s /bin/bash worker \
    && chown -R worker:worker /app /home/worker /opt/venv

USER worker

CMD ["python", "/app/runner.py"]
