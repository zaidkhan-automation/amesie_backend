FROM python:3.12-slim

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy code
COPY . /app

# Python path so "agents" resolve correctly
ENV PYTHONPATH=/app

# Install deps
RUN pip install --no-cache-dir -r requirements.txt

# Run tool server
CMD ["uvicorn", "tool_server:app", "--host", "0.0.0.0", "--port", "9000"]
