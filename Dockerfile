FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Required for collectstatic to upload to S3 during build
ARG AWS_ACCESS_KEY_ID
ARG AWS_SECRET_ACCESS_KEY
ARG AWS_STORAGE_BUCKET_NAME
ARG AWS_S3_ENDPOINT_URL
ARG STORAGE_AWS

ENV AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID} \
    AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY} \
    AWS_STORAGE_BUCKET_NAME=${AWS_STORAGE_BUCKET_NAME} \
    AWS_S3_ENDPOINT_URL=${AWS_S3_ENDPOINT_URL} \
    STORAGE_AWS=${STORAGE_AWS}

RUN DEBUG=True python manage.py collectstatic --noinput

# Non-root runtime user (defence-in-depth against in-container code execution).
RUN useradd --create-home --uid 1000 app && chown -R app:app /app
USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s \
    CMD curl -fsS http://localhost:8000/healthz || exit 1
