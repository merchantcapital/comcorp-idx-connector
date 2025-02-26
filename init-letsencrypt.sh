#!/bin/bash

# Initialize Certbot for comcorp-uat.merchantcapital.co.za
# This script sets up the initial certificates for HTTPS

# Domain name
domains=(comcorp-uat.merchantcapital.co.za)
rsa_key_size=4096
data_path="./certbot"

# Use environment variable for email if set, otherwise use empty string
if [ -z "$CERTBOT_EMAIL" ]; then
  echo "Warning: CERTBOT_EMAIL environment variable not set. Certificate expiry notifications will not be sent."
  email=""
else
  echo "Using email: $CERTBOT_EMAIL for certificate expiry notifications."
  email="$CERTBOT_EMAIL"
fi

# Check if domain is set
if [ -z "$domains" ]; then
  echo "Error: No domains set"
  exit 1
fi

# Select appropriate challenge method
staging=0 # Set to 1 for testing
if [ $staging != "0" ]; then
  staging_arg="--staging"
fi

# Create required directories
mkdir -p "$data_path/conf/live/$domains"
mkdir -p "$data_path/www"

# Create dummy certificates for initial Nginx start
echo "Creating dummy certificates for $domains..."
openssl req -x509 -nodes -newkey rsa:$rsa_key_size -days 1 \
  -keyout "$data_path/conf/live/$domains/privkey.pem" \
  -out "$data_path/conf/live/$domains/fullchain.pem" \
  -subj "/CN=localhost"

echo "Starting Nginx..."
docker-compose up -d nginx

# Delete dummy certificates
echo "Deleting dummy certificates..."
rm -Rf "$data_path/conf/live"

# Request Let's Encrypt certificates
echo "Requesting Let's Encrypt certificates for $domains..."
domain_args=""
for domain in "${domains[@]}"; do
  domain_args="$domain_args -d $domain"
done

# Join $domains to -d args
docker-compose run --rm --entrypoint "\
  certbot certonly --webroot -w /var/www/certbot \
    $staging_arg \
    $domain_args \
    --email $email \
    --rsa-key-size $rsa_key_size \
    --agree-tos \
    --force-renewal" certbot

echo "Reloading Nginx..."
docker-compose exec nginx nginx -s reload

echo "Certbot initialization completed!"
echo "Your site should now be accessible via HTTPS at https://comcorp-uat.merchantcapital.co.za"
echo "Certificates will be renewed automatically every 60 days."