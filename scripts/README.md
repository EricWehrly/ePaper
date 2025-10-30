# Setup Scripts

This directory contains setup and environment configuration scripts for the ePaper Display Project on Raspberry Pi.

## Quick Start

For a fresh Raspberry Pi setup:

```bash
# Run the complete setup (recommended)
./scripts/complete_setup.sh
```

## Directory Structure

### `complete_setup.sh`
Main orchestrator that runs all setup scripts in the correct order with health checks.

### `environment/` - System Environment Configuration
Scripts that configure the Pi's system environment (optional but helpful):

- **`setup_avahi.sh`** (requires sudo) - Configures mDNS for `.local` hostname resolution

- **`status.sh`** - Shows current system status and configuration

### `setup/` - Application Setup
Scripts for application-specific setup (SSL, ngrok, etc.):

- **`generate_ssl_cert.sh`** - Creates self-signed SSL certificates for HTTPS
- **`setup_ngrok.sh`** - Configures ngrok tunneling for Google Photos OAuth
- **`get_ngrok_url.sh`** - Utility to retrieve current ngrok URL

## Individual Script Usage

### Environment Configuration

**Avahi/mDNS Setup:**
```bash
sudo ./scripts/environment/setup_avahi.sh
```
- Fixes Docker bridge network interference
- Restricts Avahi to WiFi interface (`wlan0`) 
- Enables `raspberrypi.local` hostname access



**System Status:**
```bash
./scripts/environment/status.sh
```
- Shows network configuration, SSL status, Docker status
- Useful for troubleshooting

### Application Setup

**SSL Certificates:**
```bash
./scripts/setup/generate_ssl_cert.sh
```
- Creates SSL certificates in `config/ssl/`
- Enables HTTPS access to `https://raspberrypi.local:5000`
- Required for Google Photos OAuth (non-localhost domains need HTTPS)

**Main Setup Script:**
Runs all setup scripts in the correct order with health checks.

```bash
./scripts/complete_setup.sh
```

- Comprehensive Pi configuration
- Validates each step
- Provides troubleshooting output
- Shows final access URLs

## Troubleshooting

### Can't Access `raspberrypi.local`
```bash
# Run Avahi setup
sudo ./scripts/setup_avahi.sh

# Check if hostname resolves
getent hosts raspberrypi.local
```

### Docker Permission Denied
```bash
# Add user to docker group
./scripts/setup_docker_user.sh

# Then logout and login again
```

### HTTPS Certificate Warnings
```bash
# Regenerate SSL certificates
./scripts/generate_ssl_cert.sh

# Update Docker containers
docker compose down && docker compose up -d
```

### Services Not Starting
```bash
# Check Docker status
docker compose ps
docker compose logs -f

# Restart everything
docker compose down
./scripts/complete_setup.sh
```

## File Locations

After running setup scripts:

- **SSL Certificates**: `config/ssl/`
- **Docker Containers**: Running on ports 5000 (HTTP) and 5443 (HTTPS)
- **Avahi Config**: `/etc/avahi/avahi-daemon.conf` (backed up to `.backup`)
- **Logs**: `docker compose logs`

## Network Access

Once setup is complete, access the web interface at:

- `http://localhost:5000` (local only)
- `https://localhost:5000` (local HTTPS, self-signed cert)
- `http://raspberrypi.local:5000` (network access)
- `https://raspberrypi.local:5000` (network HTTPS, self-signed cert)

## Google Photos Integration

For Google Photos OAuth to work:

1. SSL certificates must be generated (`generate_ssl_cert.sh`)
2. Update Google Cloud Console redirect URIs to use HTTPS
3. Configure credentials in `config/google_photos_credentials.json`

See `docs/google_photos_implementation.md` for complete setup guide.