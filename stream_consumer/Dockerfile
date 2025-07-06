FROM python:3.13-alpine

WORKDIR /app

RUN apk update && apk add --no-cache gcc libpq-dev

# Copy the pyproject.toml file
COPY ../pyproject.toml ./

# Install uv
RUN pip install --no-cache-dir uv

# Install dependencies using uv into the system environment
RUN uv pip install --system .

COPY . /app/

ENV PYTHONUNBUFFERED 1

CMD ["python", "stream_consumer/consumer.py"]
