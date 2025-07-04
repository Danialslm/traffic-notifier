FROM python:3.13-alpine

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN apt update \
    && apt install -y bash \
    && rm -rf /var/cache/apt/* \
    && pip install --no-cache-dir --upgrade pip uv \
    && uv sync

RUN adduser --disabled-password --gecos "" app \
    && chown -R app:app /app
USER app
