import multiprocessing

# Gunicorn configuration file
# https://docs.gunicorn.org/en/stable/configure.html

# Server socket
bind = "127.0.0.1:8000"  # Only bind to localhost, Nginx will proxy to this

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1  # Recommended formula
worker_class = "sync"  # Use sync workers for SOAP processing
timeout = 120  # Increase timeout for SOAP requests

# Server mechanics
daemon = False  # Don't daemonize in production, use systemd instead
pidfile = "gunicorn.pid"
user = None  # Run as current user, change in production
group = None  # Run as current group, change in production
umask = 0  # File permissions

# Logging
accesslog = "access.log"
errorlog = "error.log"
loglevel = "info"

# Process naming
proc_name = "mcauto-soap-client"

# SSL (if needed)
# keyfile = "private_key.pem"
# certfile = "comcorp.cer"
# ssl_version = "TLSv1_2"
# cert_reqs = 0  # No client certificate required

# Security
limit_request_line = 4094  # Limit request line size
limit_request_fields = 100  # Limit number of header fields
limit_request_field_size = 8190  # Limit header field size