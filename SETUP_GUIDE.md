# YouTube Uploader Setup Guide

This guide will help you set up Google authentication to enable YouTube uploads in the Media Uploader application.

## Prerequisites

- A Google account
- Python 3.8+ installed
- The Media Uploader application installed

## Step 1: Create a Google Cloud Project

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Click "Select a project" at the top of the page
3. Click "New Project"
4. Enter a project name (e.g., "Media Uploader")
5. Click "Create"

## Step 2: Enable YouTube Data API v3

1. In your Google Cloud project, go to the [APIs & Services > Library](https://console.cloud.google.com/apis/library)
2. Search for "YouTube Data API v3"
3. Click on "YouTube Data API v3"
4. Click "Enable"

## Step 3: Create OAuth 2.0 Credentials

1. Go to [APIs & Services > Credentials](https://console.cloud.google.com/apis/credentials)
2. Click "Create Credentials" → "OAuth 2.0 Client IDs"
3. If prompted, configure the OAuth consent screen:
   - Choose "External" user type
   - Fill in the required fields (App name, User support email, Developer contact information)
   - Add scopes: `https://www.googleapis.com/auth/youtube.upload`
   - Add test users (your Google account email)
   - Complete the configuration

4. Back in Credentials, click "Create Credentials" → "OAuth 2.0 Client IDs"
5. Choose "Desktop application" as the application type
6. Give it a name (e.g., "Media Uploader Desktop")
7. Click "Create"

## Step 4: Download and Configure Credentials

1. After creating the OAuth 2.0 client, click the download button (⬇️) next to your client
2. Save the downloaded JSON file as `client_secret.json`
3. Create a `private` folder in your Media Uploader application directory
4. Move `client_secret.json` to the `private` folder

Your directory structure should look like this:
```
media_uploader/
├── private/
│   └── client_secret.json
├── app/
├── core/
├── services/
└── main.py
```

## Step 5: Install Dependencies

Install the required Python packages:

```bash
pip install -r requirements.txt
```

## Step 6: Test the Setup

1. Run the Media Uploader application:
   ```bash
   python main.py
   ```

2. The authentication widget should show "Setup required" initially
3. Click the "ℹ️" button to verify your setup
4. If everything is configured correctly, click "🔑 Login with Google"
5. A browser window will open for Google authentication
6. Sign in with your Google account and grant the requested permissions
7. You should see "✅ Logged in as [your-email]" in the application

## Troubleshooting

### Common Issues

**"Client secret file not found"**
- Ensure `client_secret.json` is in the `private` folder
- Check that the file name is exactly `client_secret.json` (case sensitive)

**"Invalid client secret format"**
- Make sure you downloaded the OAuth 2.0 client credentials (not service account)
- Verify the JSON file contains an "installed" section

**"Access denied" during login**
- Check that you enabled YouTube Data API v3
- Verify your OAuth consent screen is configured
- Make sure your email is added as a test user (if using external user type)

**"Quota exceeded" errors**
- YouTube Data API has daily quotas
- Check your quota usage in Google Cloud Console
- Consider requesting quota increase for production use

### File Permissions (Linux/macOS)

If you encounter permission issues:

```bash
# Set proper permissions on the private directory
chmod 700 private/
chmod 600 private/client_secret.json
```

### Windows Security

On Windows, ensure the `private` folder is not shared or accessible by other users.

## Security Notes

- Keep your `client_secret.json` file secure and never share it
- The `private` folder is automatically added to `.gitignore` to prevent accidental commits
- Credentials are stored locally and encrypted where possible
- Logout when not using the application to revoke access

## API Quotas and Limits

YouTube Data API v3 has the following limits:
- **Daily quota**: 10,000 units (default)
- **Upload quota**: Varies by account type
- **File size**: Up to 128GB per video
- **Video length**: Up to 12 hours

### Quota Usage
- Video upload: ~1,600 units
- Video listing: ~1 unit
- Channel info: ~1 unit

Monitor your quota usage in the [Google Cloud Console](https://console.cloud.google.com/apis/credentials).

## Advanced Configuration

### Custom OAuth Scopes

If you need additional permissions, modify the scopes in `core/auth_manager.py`:

```python
SCOPES = [
    'https://www.googleapis.com/auth/youtube.upload',
    'https://www.googleapis.com/auth/youtube.readonly'
]
```

### Multiple Accounts

To use multiple Google accounts:
1. Logout from the current account
2. Clear the `private` folder (except `client_secret.json`)
3. Login with the new account

### Production Deployment

For production use:
1. Set up a proper OAuth consent screen with verified domain
2. Request quota increases
3. Implement proper error handling and monitoring
4. Consider using service accounts for server-side operations

## Support

If you encounter issues:
1. Check the application logs for detailed error messages
2. Verify your Google Cloud project configuration
3. Ensure all dependencies are installed correctly
4. Check the troubleshooting section above

For additional help, refer to:
- [YouTube Data API Documentation](https://developers.google.com/youtube/v3)
- [Google OAuth 2.0 Documentation](https://developers.google.com/identity/protocols/oauth2)
- [Google Cloud Console Help](https://cloud.google.com/docs)
