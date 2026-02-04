FROM python:3.11-slim

WORKDIR /app

# Install system dependencies including Node.js for Claude Code CLI
RUN apt-get update && apt-get install -y \
    curl \
    git \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Install Claude Code CLI globally
RUN npm install -g @anthropic-ai/claude-code

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy platform core modules
COPY ../core /app/core

# Copy API code
COPY . /app/api

# Set environment variables
ENV PYTHONPATH=/app
ENV WITMIND_ROOT=/home/wit/6amdev
ENV ANTHROPIC_API_KEY=""

# Expose port
EXPOSE 4002

# Run the API
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "4002"]
