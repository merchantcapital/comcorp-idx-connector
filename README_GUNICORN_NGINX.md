# Gunicorn with Nginx Setup for mcauto-soap-client

This guide explains how to deploy the mcauto-soap-client application using Gunicorn as the WSGI server and Nginx as a reverse proxy.

## Overview

The setup consists of:
- **Flask Application**: The SOAP client and service implementation (in the `app` directory)
- **Gunicorn**: WSGI HTTP server that runs the Flask application (configuration in the `config` directory)
- **Nginx**: Web server that acts as a reverse proxy for Gunicorn (configuration in the `config` directory)
- **Certificates**: SSL certificates and keys (in the `certs` directory)

This architecture provides better performance, security, and reliability compared to running the Flask development server directly.

## Project Structure

The project is organized into the following directories:

- **app/**: Contains the application code
  - `__init__.py`: Flask application initialization
  - `provider_response_service.py`: SOAP service implementation
  - `main.py`: SOAP client implementation
  - `constants.py`: Configuration constants
  - `signature_service.py`: Signature service
  - `crypto_wsse.py`: Cryptographic functions
  - `xml.py`: XML utilities
  - `plugin.py`: Zeep plugins
  - `object_service.py`: Object service

- **config/**: Contains configuration files
  - `gunicorn_config.py`: Gunicorn configuration
  - `nginx_config`: Nginx configuration

- **certs/**: Contains certificates and keys
  - `comcorp_uat.crt`: Certificate
  - `comcorp.cer`: Certificate
  - `private_key.pem`: Private key
  - `public_key.pem`: Public key

- **wsdl/**: Contains WSDL files

## Prerequisites

- Python 3.7+
- pip (Python package manager)
- Nginx
- Virtual environment (recommended)

## Installation

1. **Clone the repository and navigate to the project directory**:
   ```bash
   git clone <repository-url>
   cd mcauto-soap-client
   ```

2. **Create and activate a virtual environment** (recommended):
   ```bash
   python -m venv .venv
   # On Windows
   .venv\Scripts\activate
   # On Linux/Mac
   source .venv/bin/activate
   ```

3. **Install the required dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Install Nginx** (if not already installed):
   - On Ubuntu/Debian:
     ```bash
     sudo apt update
     sudo apt install nginx
     ```
   - On Windows:
     Download and install from [Nginx website](http://nginx.org/en/download.html)

## Configuration

### 1. Gunicorn Configuration

The Gunicorn configuration is defined in `config/gunicorn_config.py`. Key settings include:
- Binding to 127.0.0.1:8000 (only accessible locally)
- Worker processes based on CPU count
- Timeout settings for SOAP requests
- Logging configuration

You can modify these settings based on your requirements.

### 2. Nginx Configuration

The Nginx configuration is defined in `config/nginx_config`. Key settings include:
- Listening on port 80 (and optionally 443 for HTTPS)
- Forwarding requests to Gunicorn (127.0.0.1:8000)
- Specific location for the SOAP service endpoint
- Health check endpoint

To install the Nginx configuration:

1. **Copy the configuration file to Nginx's sites-available directory**:
   ```bash
   # On Linux
   sudo cp config/nginx_config /etc/nginx/sites-available/mcauto-soap-client
   ```

2. **Create a symbolic link to enable the site**:
   ```bash
   # On Linux
   sudo ln -s /etc/nginx/sites-available/mcauto-soap-client /etc/nginx/sites-enabled/
   ```

3. **Test the configuration**:
   ```bash
   # On Linux
   sudo nginx -t
   ```

4. **Restart Nginx**:
   ```bash
   # On Linux
   sudo systemctl restart nginx
   ```

## Running the Application

### 1. Start Gunicorn

To start the application with Gunicorn:

```bash
# Activate the virtual environment if not already activated
# On Windows
.venv\Scripts\activate
# On Linux/Mac
source .venv/bin/activate

# Start Gunicorn with the configuration file
gunicorn -c config/gunicorn_config.py wsgi:app
```

### 2. Verify the Application is Running

Check if the application is running by accessing the health check endpoint:

```bash
curl http://localhost/health
```

You should receive a JSON response with status "healthy".

## Docker Deployment

The application can also be deployed using Docker, which provides an isolated and consistent environment for running the application.

### Docker Setup

The Docker setup consists of:
- **Dockerfile**: Defines the Python application container with Gunicorn
- **docker-compose.yml**: Orchestrates the Python application and Nginx containers
- **config/nginx_docker.conf**: Nginx configuration specifically for Docker

### Building and Running with Docker Compose

1. **Build and start the containers**:
   ```bash
   docker-compose up -d --build
   ```

   This command builds the Python application image and starts both the application and Nginx containers in detached mode.

2. **Check the container status**:
   ```bash
   docker-compose ps
   ```

   You should see both the web and nginx containers running.

3. **View logs**:
   ```bash
   # View logs from all containers
   docker-compose logs

   # View logs from a specific container
   docker-compose logs web
   docker-compose logs nginx
   ```

### Accessing the Application

The application is accessible at:
- http://localhost/ProviderResponseService (SOAP service endpoint)
- http://localhost/health (Health check endpoint)

### Stopping the Containers

To stop the containers:
```bash
docker-compose down
```

### Docker Troubleshooting

1. **Container not starting**:
   - Check the logs: `docker-compose logs`
   - Verify the Dockerfile and docker-compose.yml for errors

2. **Application not accessible**:
   - Ensure the containers are running: `docker-compose ps`
   - Check the Nginx configuration in config/nginx_docker.conf
   - Verify the network settings in docker-compose.yml

3. **Permission issues with mounted volumes**:
   - Check the permissions of the mounted directories
   - Ensure the application has access to the necessary files

## Production Deployment Considerations

For a production deployment, consider the following:

1. **Use a process manager** like systemd or supervisord to manage Gunicorn:
   - Automatically start on boot
   - Restart on failure
   - Log management

2. **Enable HTTPS** by uncommenting and configuring the HTTPS server block in the Nginx configuration:
   - Obtain SSL certificates (e.g., from Let's Encrypt)
   - Configure SSL settings

3. **Set up monitoring** for the application:
   - Use the health check endpoint for basic monitoring
   - Consider more advanced monitoring solutions

4. **Configure proper logging**:
   - Set up log rotation
   - Configure appropriate log levels

5. **Security considerations**:
   - Run Gunicorn as a non-root user
   - Configure firewall rules
   - Implement rate limiting in Nginx

## Systemd Service Example (Linux)

Create a systemd service file for Gunicorn:

```bash
sudo nano /etc/systemd/system/mcauto-soap-client.service
```

Add the following content (adjust paths as needed):

```ini
[Unit]
Description=Gunicorn instance to serve mcauto-soap-client
After=network.target

[Service]
User=<your-user>
Group=<your-group>
WorkingDirectory=/path/to/mcauto-soap-client
Environment="PATH=/path/to/mcauto-soap-client/.venv/bin"
ExecStart=/path/to/mcauto-soap-client/.venv/bin/gunicorn -c config/gunicorn_config.py wsgi:app

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
sudo systemctl enable mcauto-soap-client
sudo systemctl start mcauto-soap-client
```

## Troubleshooting

1. **Check Gunicorn logs**:
   - Look for errors in the Gunicorn log files (access.log and error.log)

2. **Check Nginx logs**:
   - Check /var/log/nginx/error.log for Nginx errors
   - Check /var/log/nginx/mcauto-soap-client_error.log for application-specific errors

3. **Verify connectivity**:
   - Ensure Gunicorn is running and listening on 127.0.0.1:8000
   - Ensure Nginx is running and configured correctly

4. **Test the health check endpoint**:
   - Access http://localhost/health to verify the application is responding

## Conclusion

This setup provides a robust and production-ready deployment for the mcauto-soap-client application. By using Gunicorn as the WSGI server and Nginx as a reverse proxy, you benefit from improved performance, security, and reliability.