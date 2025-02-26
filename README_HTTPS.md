# HTTPS Setup with Certbot and Nginx

This guide explains how to set up HTTPS for the mcauto-soap-client application using Certbot and Nginx. The setup is configured for the domain `comcorp-uat.merchantcapital.co.za`.

## Overview

The HTTPS setup consists of:
- **Nginx**: Web server configured as a reverse proxy with SSL/TLS support
- **Certbot**: Tool for obtaining and renewing SSL certificates from Let's Encrypt
- **Let's Encrypt**: Certificate Authority providing free SSL certificates

This setup provides secure HTTPS access to the application, which is essential for protecting sensitive data transmitted between clients and the server.

## Prerequisites

Before setting up HTTPS, ensure you have:
1. A registered domain name (comcorp-uat.merchantcapital.co.za)
2. DNS configured to point to your server's IP address
3. Ports 80 and 443 open on your firewall
4. Docker and Docker Compose installed (for Docker deployment)

## Standard Deployment (Non-Docker)

### 1. Install Certbot

On Ubuntu/Debian:
```bash
sudo apt update
sudo apt install certbot python3-certbot-nginx
```

On CentOS/RHEL:
```bash
sudo yum install epel-release
sudo yum install certbot python3-certbot-nginx
```

### 2. Obtain SSL Certificates

Run Certbot with the Nginx plugin:
```bash
sudo certbot --nginx -d comcorp-uat.merchantcapital.co.za
```

Follow the prompts to:
- Provide your email address (for renewal notifications)
- Agree to the terms of service
- Choose whether to redirect HTTP to HTTPS (recommended)

Certbot will automatically:
- Obtain certificates from Let's Encrypt
- Update your Nginx configuration
- Set up automatic renewal

### 3. Verify the Setup

Check if the certificates were installed correctly:
```bash
sudo certbot certificates
```

Test the Nginx configuration:
```bash
sudo nginx -t
```

Restart Nginx to apply changes:
```bash
sudo systemctl restart nginx
```

### 4. Set Up Automatic Renewal

Certbot installs a timer and service to automatically renew certificates. Verify it's active:
```bash
sudo systemctl status certbot.timer
```

## Docker Deployment

### 1. Prepare the Environment

Create the required directories:
```bash
mkdir -p certbot/conf certbot/www
```

### 2. Initialize Certbot

Make the initialization script executable:
```bash
chmod +x init-letsencrypt.sh
```

Edit the script to add your email address:
```bash
# Open the file
nano init-letsencrypt.sh

# Find and update the email line
email="your-email@example.com"
```

Run the initialization script:
```bash
./init-letsencrypt.sh
```

This script will:
- Create temporary certificates
- Start Nginx
- Obtain real certificates from Let's Encrypt
- Configure Nginx to use the certificates

### 3. Start the Application

Start the application with Docker Compose:
```bash
docker-compose up -d
```

This will start:
- The web application container
- The Nginx container with HTTPS configured
- The Certbot container for automatic certificate renewal

### 4. Verify the Setup

Check if the containers are running:
```bash
docker-compose ps
```

Access your application via HTTPS:
```
https://comcorp-uat.merchantcapital.co.za
```

## Certificate Renewal

### Standard Deployment

Certbot automatically creates a systemd timer to renew certificates. You can manually trigger a renewal:
```bash
sudo certbot renew
```

### Docker Deployment

The Docker setup includes automatic renewal:
- The Certbot container attempts renewal every 12 hours
- The Nginx container reloads every 6 hours to pick up new certificates

You can manually trigger a renewal:
```bash
docker-compose run --rm certbot renew
docker-compose exec nginx nginx -s reload
```

## Troubleshooting

### Certificate Issues

If certificates aren't being issued:
1. Check DNS configuration
2. Ensure ports 80 and 443 are open
3. Check Certbot logs:
   ```bash
   # Standard deployment
   sudo journalctl -u certbot
   
   # Docker deployment
   docker-compose logs certbot
   ```

### Nginx Configuration Issues

If Nginx isn't serving HTTPS correctly:
1. Check Nginx configuration:
   ```bash
   # Standard deployment
   sudo nginx -t
   
   # Docker deployment
   docker-compose exec nginx nginx -t
   ```
2. Check Nginx logs:
   ```bash
   # Standard deployment
   sudo tail -f /var/log/nginx/error.log
   
   # Docker deployment
   docker-compose logs nginx
   ```

## Security Considerations

This setup includes:
- Modern TLS protocols (TLSv1.2 and TLSv1.3)
- Strong cipher suites
- SSL session caching
- SSL stapling

For enhanced security:
1. Consider implementing HTTP Strict Transport Security (HSTS)
2. Regularly update Nginx and Certbot
3. Monitor certificate expiration dates

## Conclusion

Your application is now configured to use HTTPS with automatically renewed SSL certificates from Let's Encrypt. This provides secure communication between clients and your server, protecting sensitive data in transit.