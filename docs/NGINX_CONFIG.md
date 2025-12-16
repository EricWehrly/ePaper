# Nginx Configuration for ePaper

## Upload Size Limit

To support large image uploads (playlists with multiple images), nginx needs to be configured to accept larger payloads.

### Required Setting

Add this to your nginx configuration (in the `http`, `server`, or `location` block):

```nginx
client_max_body_size 200M;
```

### Example Configuration

```nginx
server {
    listen 80;
    server_name epaper.whirlwind.family;
    
    # Allow large file uploads for image bundles
    client_max_body_size 200M;
    
    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts for large uploads
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }
}
```

### After Updating

Restart nginx to apply changes:
```bash
sudo nginx -t  # Test configuration
sudo systemctl reload nginx  # Reload if test passes
```

## Current Status

- **Flask App**: Configured for 200MB max upload ✅
- **Infrastructure Template**: Updated with 200MB limit ✅
- **Live Server**: Needs redeployment to apply new nginx config
- **Client**: Automatically batches files and falls back to one-at-a-time if needed ✅

## Applying the Fix

### Option 1: Redeploy Infrastructure (Recommended)
```bash
cd infrastructure
terraform apply  # Will recreate EC2 with new nginx config
```

### Option 2: Manual Update (Quick Fix)
SSH into the EC2 instance and edit `/etc/nginx/conf.d/chisel.conf`:
```bash
# Add after 'server_name' line:
client_max_body_size 200M;

# Then reload nginx
sudo nginx -t
sudo systemctl reload nginx
```
