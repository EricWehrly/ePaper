#!/bin/bash

# Update system
yum update -y

# Install dependencies
yum install -y docker python3-pip
amazon-linux-extras install -y nginx1

# Install certbot via pip3 (more reliable on Amazon Linux 2)
pip3 install certbot certbot-nginx

# Start and enable Docker
systemctl start docker
systemctl enable docker
usermod -a -G docker ec2-user

# Create chisel service using Docker
cat > /etc/systemd/system/chisel-server.service << 'EOF'
[Unit]
Description=Chisel Server
After=docker.service
Requires=docker.service

[Service]
Type=simple
User=root
ExecStartPre=/usr/bin/docker pull jpillora/chisel:latest
ExecStart=/usr/bin/docker run --rm --name chisel-server \
  -p 8080:8080 \
  -p 5000:5000 \
  -p 443:443 \
  jpillora/chisel:latest server \
  --host 0.0.0.0 \
  --port 8080 \
  --reverse \
  --auth ${chisel_auth}
ExecStop=/usr/bin/docker stop chisel-server
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# Start Chisel server
systemctl daemon-reload
systemctl enable chisel-server
systemctl start chisel-server

# Configure nginx as reverse proxy (HTTP only initially, SSL added by certbot)
cat > /etc/nginx/conf.d/chisel.conf << 'EOF'
server {
    listen 80;
    server_name ${domain_name};
    
    # Proxy to local ePaper app (forwarded by Chisel client)
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
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
/usr/local/bin/certbot --nginx -d ${domain_name} --non-interactive --agree-tos --email admin@${domain_name} --redirect

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
systemctl status docker --no-pager >> /var/log/user-data.log

# Test Chisel server connectivity
echo "Testing Chisel server connectivity:" >> /var/log/user-data.log
curl -k https://localhost:8080 >> /var/log/user-data.log 2>&1 || echo "Chisel server not responding on 8080" >> /var/log/user-data.log