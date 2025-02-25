FROM nvidia/cuda:12.3.2-cudnn9-runtime-ubuntu22.04

# Setup Python e dipendenze di sistema
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-dev \
    gcc \
    g++ \
    mkvtoolnix \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Installazione delle dipendenze Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

WORKDIR /app
COPY . .

RUN ln -s /usr/bin/python3 /usr/bin/python

CMD ["python3", "AudioMediaChecker.py"]
