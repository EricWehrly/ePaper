#!/bin/bash

# Update system
yum update -y

# Install dependencies
yum install -y docker nginx certbot python3-certbot-nginx

# Start and enable Docker
systemctl start docker
systemctl enable docker
usermod -a -G docker ec2-user

# Install inlets server
curl -sLS https://get.inlets.dev | sh
mv inlets /usr/local/bin/

# Create inlets service
cat > /etc/systemd/system/inlets-server.service << 'EOF'
[Unit]
Description=Inlets Server
After=network.target

[Service]
Type=simple
User=root
ExecStart=/usr/local/bin/inlets server \
  --port=8123 \
  --token=${inlets_token}
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# Start inlets server
systemctl daemon-reload
systemctl enable inlets-server
systemctl start inlets-server

# Configure nginx as reverse proxy
cat > /etc/nginx/conf.d/inlets.conf << 'EOF'
server {
    listen 80;
    server_name ${domain_name};

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name ${domain_name};

    # SSL configuration will be added by certbot
    
    # Proxy to inlets tunnel
    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support (if needed)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
EOF

# Start nginx
systemctl start nginx
systemctl enable nginx

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

# Get SSL certificate from Let's Encrypt
echo "Requesting SSL certificate for ${domain_name}..."
certbot --nginx -d ${domain_name} --non-interactive --agree-tos --email admin@${domain_name} --redirect

# Set up automatic certificate renewal
echo "0 0,12 * * * root python3 -c 'import random; import time; time.sleep(random.random() * 3600)' && certbot renew -q" | sudo tee -a /etc/crontab > /dev/null

# Create a simple health check endpoint
mkdir -p /var/www/html
echo "OK" > /var/www/html/health

# Log completion
echo "Inlets server setup completed at $(date)" >> /var/log/user-data.log