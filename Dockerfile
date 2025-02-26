FROM python:3.9-slim

WORKDIR /app

# Install system dependencies required for xmlsec
RUN apt-get update && apt-get install -y \
    libxml2-dev \
    libxmlsec1-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/
COPY config/ ./config/
COPY certs/ ./certs/

# Create wsdl directory
RUN mkdir -p ./wsdl/

# Copy wsdl files if they exist (will be ignored if directory is empty)
COPY wsdl/ ./wsdl/

COPY wsgi.py .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Expose the port Gunicorn will listen on
EXPOSE 8000

# Run Gunicorn
CMD ["gunicorn", "-c", "config/gunicorn_config.py", "wsgi:app"]