# ==============================
# Stage 1 — Builder
# ==============================
FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install build dependencies (only in builder stage)
RUN apt-get update && apt-get install -y \
    build-essential \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip first
RUN pip install --upgrade pip

# Copy only requirements first (better caching)
COPY requirements.txt .

# Install dependencies into a separate directory
RUN pip install --no-cache-dir \
    --prefix=/install \
    -r requirements.txt


# ==============================
# Stage 2 — Runtime (Small)
# ==============================
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install only runtime system dependencies
RUN apt-get update && apt-get install -y \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy installed Python packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY . .

# If using rembg or model downloads
ENV U2NET_HOME=/tmp/.u2net

# Cloud Run provides PORT env variable
ENV PORT=8080

# Start ADK Web
CMD ["sh", "-c", "adk web --host 0.0.0.0 --port ${PORT}"]
