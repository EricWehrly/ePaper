# Setup Scripts

This directory contains automated setup scripts for the ePaper Display Project on Raspberry Pi.

## Quick Start

For a fresh Raspberry Pi setup:

```bash
# Run the complete setup (recommended)
./scripts/complete_setup.sh
```

## Individual Scripts

### 1. `generate_ssl_cert.sh`
Creates self-signed SSL certificates for HTTPS development.

```bash
./scripts/generate_ssl_cert.sh
```

- Creates SSL certificates in `config/ssl/`
- Enables HTTPS access to `https://raspberrypi.local:5000`
- Required for Google Photos OAuth (non-localhost domains need HTTPS)

### 2. `setup_avahi.sh` (requires sudo)
Configures mDNS/Avahi for proper `.local` hostname resolution.

```bash
sudo ./scripts/setup_avahi.sh
```

- Fixes Docker bridge network interference
- Restricts Avahi to WiFi interface (`wlan0`)
- Enables `raspberrypi.local` hostname access

### 3. `setup_docker_user.sh`
Adds user to docker group for passwordless Docker commands.

```bash
./scripts/setup_docker_user.sh
```

- One-time setup per user
- **Requires logout/login** to take effect
- Eliminates need for `sudo docker`

### 4. `complete_setup.sh`
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