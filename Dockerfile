FROM python:3.9-slim

WORKDIR /app

# Install system dependencies required for Python packages
RUN apt-get update && apt-get install -y \
    libxml2-dev \
    libxmlsec1-dev \
    libxslt-dev \
    libssl-dev \
    pkg-config \
    gcc \
    build-essential \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/
COPY config/ ./config/
COPY certs/ ./certs/

# Create wsdl directory and ensure it has correct permissions
RUN mkdir -p ./wsdl/ && chmod 777 ./wsdl/

# Copy WSDL files - these will be overridden by volume mounts if present
COPY wsdl/ ./wsdl/
COPY wsgi.py .

# Ensure all directories have correct permissions
RUN chmod -R 755 /app

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Expose the port Gunicorn will listen on
EXPOSE 8000

# Run Gunicorn
CMD ["gunicorn", "-c", "config/gunicorn_config.py", "wsgi:app"]