FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libopencv-dev \
    python3-opencv \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p pic pic-raw logs config

ENV FLASK_APP=src/main.py
ENV FLASK_ENV=development
ENV PYTHONPATH=/app

EXPOSE 5000

COPY docker-entrypoint.sh .
RUN chmod +x docker-entrypoint.sh

CMD ["./docker-entrypoint.sh"]
