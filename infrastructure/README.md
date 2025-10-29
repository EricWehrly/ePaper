# ePaper Inlets Infrastructure

This Terraform configuration sets up an AWS-based inlets tunnel to replace ngrok for the ePaper project. It provides a self-managed, reliable tunnel solution with your own domain.

## Architecture

```
Raspberry Pi (ePaper) → Inlets Client → Internet → AWS (Inlets Server) → Your Domain
```

### Components Created

- **VPC with public subnet** - Isolated network for the inlets server
- **EC2 instance** - Runs the inlets server with nginx reverse proxy
- **Elastic IP** - Stable public IP address
- **Route 53 DNS record** - Points your domain to the server
- **SSL Certificate** - Automatic Let's Encrypt certificate via ACM
- **Security Group** - Firewall rules for HTTP/HTTPS/SSH access

## Prerequisites

1. **AWS Account** with appropriate permissions
2. **Domain registered** with Route 53 hosted zone
3. **AWS CLI configured** with your credentials
4. **Terraform installed** (>= 1.0)
5. **AWS Key Pair created** for EC2 SSH access

## Setup Instructions

### 1. Configure Variables

Copy the example variables file and customize it:

```bash
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars` with your values:

```hcl
domain_name     = "epaper.yourdomain.com"    # Your subdomain
hosted_zone_id  = "Z1234567890ABCD"          # Your Route 53 zone ID
key_name        = "your-aws-key-pair-name"   # Your AWS key pair
inlets_token    = "very-long-secure-random-token-here"  # Generate securely
```

**Important**: Generate a secure random token for `inlets_token`:
```bash
openssl rand -hex 32
```

### 2. Deploy Infrastructure

```bash
terraform apply
```

That's it! Terraform will initialize, plan, and deploy everything.

#### Option A: Terraform-managed (recommended)
Add to your `terraform.tfvars`:
```hcl
generate_client_config = true
```

Then re-run:
```bash
terraform apply
```

This creates `infrastructure/.env.inlets` with your credentials.

#### Option B: Manual
```bash
# Get your token
terraform output inlets_token

# Create .env.inlets manually with the token
```

#### Start the client
Copy these files to your Raspberry Pi:
- `infrastructure/docker-compose.inlets.yml`
- `infrastructure/.env.inlets`

Then run:
```bash
docker compose -f docker-compose.inlets.yml up -d
```

### 4. Update ePaper Configuration

Update your ePaper project to use the new domain instead of ngrok:

1. **Update OAuth redirect URIs** in Google Cloud Console to use `https://epaper.yourdomain.com`
2. **Remove ngrok configuration** from docker-compose.yml
3. **Update any hardcoded ngrok references** to use your domain

## Verification

1. **Check server status**: SSH to the server and verify services
   ```bash
   ssh -i /path/to/your/key.pem ec2-user@$(terraform output -raw inlets_server_public_ip)
   sudo systemctl status inlets-server nginx
   ```

2. **Test tunnel**: Access your domain in a browser
   ```bash
   curl https://epaper.yourdomain.com
   ```

3. **Monitor logs** on Raspberry Pi:
   ```bash
   sudo journalctl -u inlets-client -f
   ```

## Cost Estimate

- **EC2 t3.micro**: ~$8.50/month (free tier eligible for 12 months)
- **Elastic IP**: $0 (while attached to running instance)
- **Route 53**: $0.50/month per hosted zone + $0.40 per million queries
- **Data transfer**: ~$0.09/GB out

**Total**: ~$9/month (much less than ngrok Pro)

## Security Notes

1. **Restrict SSH access**: Update `allowed_ssh_cidrs` in terraform.tfvars to your IP range
2. **Token security**: Keep your inlets token secure and rotate it periodically
3. **Monitor access**: Check CloudWatch logs for unusual activity
4. **Updates**: Regularly update the EC2 instance with security patches

## Maintenance

### Update inlets
```bash
# On the server
sudo systemctl stop inlets-server
curl -sLS https://get.inlets.dev | sh
sudo mv inlets /usr/local/bin/
sudo systemctl start inlets-server
```

### Rotate token
1. Generate new token: `openssl rand -hex 32`
2. Update terraform.tfvars
3. Run: `terraform apply`
4. Update client configuration on Raspberry Pi
5. Restart client service

### SSL Certificate
Certificates are automatically renewed by certbot. Check renewal:
```bash
sudo certbot certificates
```

## Troubleshooting

### Common Issues

1. **DNS not resolving**: Wait 5-10 minutes for DNS propagation
2. **SSL certificate failed**: Check domain ownership and DNS settings
3. **Tunnel not connecting**: Verify token matches between server and client
4. **502 Bad Gateway**: Check if inlets client is running on Raspberry Pi

### Logs to Check

- **Server logs**: `sudo journalctl -u inlets-server -f`
- **Client logs**: `sudo journalctl -u inlets-client -f`
- **Nginx logs**: `sudo tail -f /var/log/nginx/error.log`
- **Certbot logs**: `sudo tail -f /var/log/letsencrypt/letsencrypt.log`

## Cleanup

To destroy all resources:
```bash
terraform destroy
```

**Warning**: This will permanently delete all AWS resources created by this configuration.