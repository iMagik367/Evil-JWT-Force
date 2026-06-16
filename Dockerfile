# Use Python 3.11 slim image as base
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    MODEL_PATH=/app/models/jwt_analyzer.pt \
    LOG_LEVEL=INFO

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Create necessary directories
RUN mkdir -p /app/models /app/logs /app/static /app/media

# Set permissions
RUN chown -R nobody:nogroup /app

# Switch to non-root user
USER nobody

# Expose port
EXPOSE 8000

# Run the application
CMD ["python", "-m", "ai_module.api"]

# Adiciona metadados para a imagem
LABEL maintainer="EVIL_JWT_FORCE Team" \
      version="1.0" \
      description="Ferramenta de teste de segurança para JWT e injeção SQL" 