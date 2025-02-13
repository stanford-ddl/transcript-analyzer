FROM mcr.microsoft.com/devcontainers/python:3.11

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install base Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
