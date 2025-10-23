# Google Cloud Setup - Complete Guide

## Overview: User Authentication vs Developer Authentication

**Important**: This setup allows **any Google user** to authenticate with your ePaper display, not just you as the developer. Each user will log in with their own Google account and select photos from their own Google Photos library.

## Step-by-Step Google Cloud Setup

### 1. Create Google Cloud Project

1. **Go to [Google Cloud Console](https://console.cloud.google.com/)**
2. **Click "New Project"** 
   - Project name: `ePaper Photo Display` (or similar)
   - Leave organization blank (unless you have one)
   - Click "Create"
3. **Note the Project ID** - you'll need this later

### 2. Enable Required APIs

1. **Navigate to "APIs & Services" → "Library"**
2. **Search and enable these APIs:**
   - `Photos Library API` - Click "Enable"
   - `Google Photos Picker API` - Click "Enable" 

### 3. Configure OAuth Consent Screen (Critical Step)

This step determines who can use your application:

1. **Go to "APIs & Services" → "OAuth consent screen"**
2. **Choose User Type:**
   - **External** ✅ - Allows any Google user to authenticate
   - ~~Internal~~ - Only for Google Workspace organizations
3. **Fill Required Information:**
   ```
   App name: ePaper Photo Display
   User support email: [your email]
   Logo: [optional - can upload later]
   
   App domain: [leave blank for now]
   Authorized domains: [leave blank]
   
   Developer contact info: [your email]
   ```
4. **Scopes Section:**
   - Click "Add or Remove Scopes"
   - **Manual entry**: Add `https://www.googleapis.com/auth/photospicker.mediaitems.readonly`
   - This allows read-only access to photos users explicitly select
5. **Test Users (for development):**
   - Add your own email address
   - Add any other emails you want to test with
   - In production, you can remove test users to allow any Google user

### 4. Create OAuth 2.0 Credentials

1. **Go to "APIs & Services" → "Credentials"**
2. **Click "Create Credentials" → "OAuth 2.0 Client ID"**
3. **Configure:**
   ```
   Application type: Web application
   Name: ePaper Display Client
   
   Authorized JavaScript origins: [leave empty]
   
   Authorized redirect URIs:
   http://localhost:5000/oauth/callback
   http://127.0.0.1:5000/oauth/callback
   http://your-raspberry-pi.local:5000/oauth/callback
   http://192.168.1.100:5000/oauth/callback  [your actual Pi IP]
   ```

   **Note**: Add multiple redirect URIs to handle different access scenarios:
   - `localhost` - for local development
   - `127.0.0.1` - alternative local access  
   - `your-pi-hostname.local` - for local network access by hostname
   - `192.168.1.x` - for direct IP access

4. **Download the JSON file** - this contains your client credentials

## Network Access Options

Google OAuth requires HTTPS for non-localhost domains. Choose your setup:

### Option A: SSH Tunnel (Development)
```bash
# Access Pi via localhost tunnel (no HTTPS needed)
ssh -L 5000:localhost:5000 pi@your-pi-ip

# Google Cloud Console settings:
Authorized JavaScript Origins: http://localhost:5000
Authorized Redirect URIs: http://localhost:5000/oauth/callback
```

### Option B: ngrok (Recommended for Testing)
```bash
# On your Pi - install ngrok
curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc
echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | sudo tee /etc/apt/sources.list.d/ngrok.list
sudo apt update && sudo apt install ngrok

# Get free auth token from ngrok.com
ngrok config add-authtoken YOUR_NGROK_TOKEN

# Expose your app (get HTTPS URL)
ngrok http 5000
```

**Use the ngrok HTTPS URL in Google Cloud Console:**
```
Authorized JavaScript Origins: https://abc123.ngrok-free.app
Authorized Redirect URIs: https://abc123.ngrok-free.app/oauth/callback
```

### Option C: Local HTTPS (Advanced)
Set up reverse proxy with SSL certificates for permanent local network access.

### 5. Configure Application Credentials

1. **Copy credentials to your project:**
   ```bash
   # Rename and copy the downloaded file
   cp ~/Downloads/client_secret_*.json config/google_photos_credentials.json
   ```

2. **Update config/settings.json:**
   ```json
   {
     "google_photos": {
       "client_id": "123456789-abcdef.apps.googleusercontent.com",
       "client_secret": "GOCSPX-your_actual_secret_here", 
       "redirect_path": "/oauth/callback",
       "scopes": ["https://www.googleapis.com/auth/photospicker.mediaitems.readonly"]
     }
   }
   ```

   **Extract these values from your downloaded JSON:**
   - `client_id` → `"client_id"` field
   - `client_secret` → `"client_secret"` field

## Authentication Flow Explanation

### What Happens When a User Authenticates:

1. **User visits your ePaper display web interface**
2. **User clicks "Connect Google Photos"** 
3. **User is redirected to Google's authentication server**
4. **Google asks user:** "Do you want to allow 'ePaper Photo Display' to access photos you select?"
5. **User clicks "Allow"** (or "Deny")
6. **User is redirected back to your application**
7. **Your app can now access photos the user explicitly selects**

### Security & Privacy Notes:

- ✅ **Users authenticate with their own Google accounts**
- ✅ **Users only grant access to photos they explicitly select**
- ✅ **Your app cannot browse their entire photo library**
- ✅ **Users can revoke access anytime in their Google Account settings**
- ✅ **No passwords or personal info stored in your app**

## Testing the Setup

### Verify API Access:
```bash
# Check if APIs are enabled
curl "https://photoslibrary.googleapis.com/v1/albums" \
  -H "Authorization: Bearer [test-token]"
```

### Test OAuth Flow:
1. Start your Docker container
2. Visit `http://your-pi-ip:5000`
3. Click "Connect Google Photos"  
4. Complete Google authentication
5. Verify you're redirected back successfully

## Production Considerations

### Publishing Your App (Optional):
If you want to remove the "unverified app" warning:
1. **Go to OAuth consent screen**
2. **Click "Publish App"** 
3. **Submit for verification** (requires Google review)

### For Personal/Family Use:
- Keep app in "Testing" mode
- Add family members as "Test Users"
- No verification needed

### Rate Limits:
- **10,000 API calls/day** (sessions, polling)
- **75,000 photo downloads/day**
- Sufficient for personal use

## Troubleshooting

### "Unverified App" Warning:
- **Expected** for development/personal use
- Users can click "Advanced" → "Go to [app name] (unsafe)"
- Or submit app for Google verification

### "redirect_uri_mismatch" Error:
- Check your redirect URIs in Google Cloud Console
- Ensure the URL matches exactly (including port)
- Add additional URIs as needed

### Permission Denied Errors:
- Verify APIs are enabled
- Check OAuth consent screen configuration
- Ensure user is added as test user (if in testing mode)

---

## Summary

This setup creates an OAuth application that:
- ✅ Allows any Google user to authenticate securely
- ✅ Grants access only to photos users explicitly select  
- ✅ Works from any device on your network
- ✅ Maintains user privacy and security
- ✅ Follows Google's best practices for photo access

The key insight is that **users authenticate themselves** - your ePaper display acts as a secure photo selection and display interface for whoever is using it.