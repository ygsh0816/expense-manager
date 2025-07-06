# Dockerfile
FROM python:3.13-alpine

WORKDIR /app

# Install system deps for psycopg and build tools
RUN apk update && apk add --no-cache gcc libpq-dev musl-dev bash

# Copy dependency files first (for caching)
COPY pyproject.toml ./

# Install poetry and dependencies (using uv tool or poetry directly)
RUN pip install --no-cache-dir uv
RUN uv pip install --system .

# Copy whole project source
COPY . /app/

# Make entrypoint executable
RUN chmod +x /app/entrypoint.sh

ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=xcnt.settings

EXPOSE 8000
