#!/bin/bash

# Update system
dnf update -y

# Install dependencies (AL2023 uses dnf, not yum)
dnf install -y docker python3-pip nginx

# Install certbot (no urllib3 constraint needed - AL2023 has modern OpenSSL)
# Updated: 2025-12-14 - Retrying SSL certificate after rate limit expiration
pip3 install certbot certbot-nginx
# Install AWS CLI for S3 certificate cache operations
dnf install -y awscli || pip3 install awscli

# Install Chisel server
CHISEL_VERSION="1.9.1"
curl -L "https://github.com/jpillora/chisel/releases/download/v$${CHISEL_VERSION}/chisel_$${CHISEL_VERSION}_linux_amd64.gz" -o /tmp/chisel.gz
gunzip /tmp/chisel.gz
chmod +x /tmp/chisel
mv /tmp/chisel /usr/local/bin/chisel

# Create Chisel server systemd service file
cat > /etc/systemd/system/chisel-server.service << 'EOF'
[Unit]
Description=Chisel Server Tunnel
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStart=/usr/local/bin/chisel server --auth ${CHISEL_AUTH} --port 8080 --reverse
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Start Chisel server
systemctl daemon-reload
systemctl enable chisel-server
systemctl start chisel-server

# Configure nginx placeholder config (won't start yet, just set the config)
cat > /etc/nginx/conf.d/chisel.conf << 'EOF'
server {
    listen 80;
    server_name DOMAIN_NAME;
    
    # Allow large file uploads for image bundles
    client_max_body_size 200M;
    
    # Proxy to local ePaper app (forwarded by Chisel client)
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts for large uploads
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
        
        # WebSocket support (if needed)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
    
    # Health check endpoint
    location /health {
        access_log off;
        return 200 "OK\n";
        add_header Content-Type text/plain;
    }
}
EOF

# Replace domain name in placeholder config
sed -i "s/DOMAIN_NAME/${domain_name}/g" /etc/nginx/conf.d/chisel.conf

# DO NOT START NGINX YET - wait until certificate is obtained and config is finalized

# Wait for DNS to propagate before requesting SSL certificate
echo "Waiting for DNS propagation for ${domain_name}..."
DNS_READY=false
MAX_ATTEMPTS=30
ATTEMPT=0

while [ "$DNS_READY" = false ] && [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    ATTEMPT=$((ATTEMPT + 1))
    echo "DNS check attempt $ATTEMPT/$MAX_ATTEMPTS..."
    
    # Check if our domain resolves to this instance's public IP
    RESOLVED_IP=$(dig +short ${domain_name} @8.8.8.8 | head -n1)
    INSTANCE_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)
    
    if [ "$RESOLVED_IP" = "$INSTANCE_IP" ]; then
        echo "DNS resolution confirmed: ${domain_name} -> $INSTANCE_IP"
        DNS_READY=true
    else
        echo "DNS not ready yet. Resolved: '$RESOLVED_IP', Expected: '$INSTANCE_IP'"
        sleep 30
    fi
done

if [ "$DNS_READY" = false ]; then
    echo "WARNING: DNS did not resolve after $MAX_ATTEMPTS attempts. Proceeding anyway..."
fi

CERT_ARCHIVE="${CERT_ARCHIVE}"
S3_BUCKET="${letsencrypt_bucket}"

# Validate inputs passed from Terraform
if [ -z "${CERT_ARCHIVE}" ] || [ "${CERT_ARCHIVE}" = "${domain_name}.tar.gz" -a -z "${CERT_ARCHIVE}" ]; then
    echo "ERROR: CERT_ARCHIVE is empty or not set. Aborting setup."
    exit 1
fi

if [ -z "${letsencrypt_bucket}" ]; then
    echo "WARNING: letsencrypt_bucket is not set. Certificate caching to S3 will be disabled."
    USE_S3=false
else
    USE_S3=true
fi

# Ensure awscli is available when we intend to use S3
if [ "$USE_S3" = "true" ]; then
    if ! command -v aws >/dev/null 2>&1; then
        echo "WARNING: awscli not installed; S3 restore/upload will be skipped."
        USE_S3=false
    fi
fi

echo "Checking for existing certificate for ${domain_name}..."
if [ -d "/etc/letsencrypt/live/${domain_name}" ]; then
    echo "Certificate already present on disk; skipping issuance."
    HAVE_CERT=true
else
    # Try restore from S3 cache
    if aws s3 ls "s3://${letsencrypt_bucket}/${CERT_ARCHIVE}" >/dev/null 2>&1; then
        echo "Found cached certificate bundle in s3://${letsencrypt_bucket}/${CERT_ARCHIVE}, restoring..."
        aws s3 cp "s3://${letsencrypt_bucket}/${CERT_ARCHIVE}" /tmp/${CERT_ARCHIVE}
        mkdir -p /etc/letsencrypt
        tar -xzf /tmp/${CERT_ARCHIVE} -C /etc/letsencrypt
        chmod -R 700 /etc/letsencrypt
        chown -R root:root /etc/letsencrypt
        rm -f /tmp/${CERT_ARCHIVE}
        HAVE_CERT=true
    else
        HAVE_CERT=false
    fi
fi

if [ "${enable_certbot_staging}" = "true" ]; then
    STAGING_FLAG="--staging"
else
    STAGING_FLAG=""
fi

if [ "$HAVE_CERT" = "false" ]; then
    echo "No cached certificate found; attempting to obtain one using certbot (staging=${enable_certbot_staging})..."

    # Ensure nginx is stopped for standalone challenge
    systemctl stop nginx || true

    if /usr/local/bin/certbot certonly --standalone $STAGING_FLAG -d ${domain_name} --non-interactive --agree-tos --email admin@${domain_name}; then
        echo "Certbot obtained certificate successfully."
        # Package and upload to S3 for future reuse
        tar -czf /tmp/${CERT_ARCHIVE} -C /etc/letsencrypt .
        aws s3 cp /tmp/${CERT_ARCHIVE} "s3://${letsencrypt_bucket}/${CERT_ARCHIVE}"
        HAVE_CERT=true
    else
        echo "WARNING: certbot failed to obtain certificate. Will fall back to HTTP-only config."
        HAVE_CERT=false
    fi
fi

if [ "$HAVE_CERT" = "true" ]; then
    echo "Configuring nginx with HTTPS..."
    
    # Generate SSL configuration files if they don't exist (certbot --standalone doesn't create them)
    if [ ! -f /etc/letsencrypt/options-ssl-nginx.conf ]; then
        mkdir -p /etc/letsencrypt
        cat > /etc/letsencrypt/options-ssl-nginx.conf <<'SSL_CONF'
# Mozilla Intermediate configuration
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384;
ssl_prefer_server_ciphers off;
ssl_session_timeout 1d;
ssl_session_cache shared:SSL:10m;
ssl_session_tickets off;
ssl_stapling on;
ssl_stapling_verify on;
SSL_CONF
    fi
    
    if [ ! -f /etc/letsencrypt/ssl-dhparams.pem ]; then
        # Use a 2048-bit DH param (faster generation, still secure)
        openssl dhparam -out /etc/letsencrypt/ssl-dhparams.pem 2048 2>/dev/null || echo "Warning: Could not generate dhparams"
    fi
    
    cat > /etc/nginx/conf.d/chisel.conf <<'EOF'
# HTTP server - redirect to HTTPS
server {
    listen 80;
    server_name DOMAIN_NAME;
    
    # Redirect all HTTP to HTTPS
    return 301 https://$host$request_uri;
}

# HTTPS server - the actual service
server {
    listen 443 ssl;
    http2 on;
    server_name DOMAIN_NAME;

    # SSL certificate paths (managed by certbot)
    ssl_certificate /etc/letsencrypt/live/DOMAIN_NAME/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/DOMAIN_NAME/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    # Allow large file uploads (200MB)
    client_max_body_size 200M;
    
    # Proxy all requests to app (forwarded by Chisel from client on port 5000)
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 86400;
        
        # Timeouts for large uploads
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
    }
    
    # Health check endpoint
    location /health {
        access_log off;
        return 200 "OK\n";
        add_header Content-Type text/plain;
    }
}
EOF
    # Replace DOMAIN_NAME placeholders
    sed -i "s/DOMAIN_NAME/${domain_name}/g" /etc/nginx/conf.d/chisel.conf
else
    # Certificate failed (probably rate limit), keep HTTP-only config already written
    echo "WARNING: Failed to obtain SSL certificate. Keeping HTTP-only nginx..."
    # Config already in place from earlier, no changes needed
fi

# Test nginx configuration
if ! nginx -t; then
    echo "ERROR: nginx configuration test failed"
    cat /etc/nginx/conf.d/chisel.conf
    journalctl -u nginx -n 50
    exit 1
fi

# Enable and restart nginx (to reload HTTPS configuration if cert was obtained)
systemctl enable nginx
systemctl restart nginx

# Verify nginx is running
sleep 5
if systemctl is-active --quiet nginx; then
    echo "✓ nginx is running successfully"
else
    echo "ERROR: nginx failed to start"
    journalctl -u nginx -n 50
    exit 1
fi

# Set up automatic certificate renewal
echo "0 0,12 * * * root python3 -c 'import random; import time; time.sleep(random.random() * 3600)' && /usr/local/bin/certbot renew -q" | sudo tee -a /etc/crontab > /dev/null

# Create a simple health check endpoint
mkdir -p /var/www/html
echo "OK" > /var/www/html/health

# Log completion
echo "Chisel server setup completed at $(date)" >> /var/log/user-data.log

# Log service status for debugging
echo "Service statuses:" >> /var/log/user-data.log
systemctl status chisel-server --no-pager >> /var/log/user-data.log
systemctl status nginx --no-pager >> /var/log/user-data.log
