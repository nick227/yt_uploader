# Distribution Guide

This guide explains how to distribute the Media Uploader application to other users.

## Google API Credentials Options

### Option 1: User-Provided Credentials (Recommended)

Each user provides their own Google API credentials, allowing them to:
- Upload to their own YouTube channels
- Use their own API quota
- Maintain security of their credentials

#### How it works:
1. Users click "Setup" in the authentication widget
2. They can either:
   - Enter credentials manually
   - Import from a `client_secret.json` file
3. The app stores credentials securely in the `private/` folder
4. Users authenticate with their own Google accounts

#### Benefits:
- ✅ No API quota sharing
- ✅ Users upload to their own channels
- ✅ No security concerns
- ✅ No verification requirements for distribution
- ✅ Each user manages their own credentials

#### Setup Instructions for Users:
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the YouTube Data API v3
4. Go to "Credentials" → "Create Credentials" → "OAuth 2.0 Client IDs"
5. Choose "Desktop application" as the application type
6. Download the `client_secret.json` file
7. In the app, click "Setup" and either:
   - Import the downloaded file, OR
   - Enter the credentials manually

### Option 2: Shared Credentials (Current Setup)

The app uses your personal Google API credentials:
- All uploads go to your YouTube channel
- All API calls count against your quota
- Only you (as a test user) can authenticate

#### Limitations:
- ❌ Only you can use the app
- ❌ All uploads go to your channel
- ❌ Your API quota is shared
- ❌ Requires verification for distribution
- ❌ Security concerns with shared credentials

## Distribution Recommendations

### For Personal Use or Small Teams:
Use **Option 1 (User-Provided Credentials)**. This is the most secure and scalable approach.

### For Enterprise/Organization Use:
Consider creating a shared Google Cloud project with:
- Organization-wide API quota
- Centralized credential management
- Custom OAuth consent screen with your organization's branding

## Building for Distribution

### 1. Build the Executable
```bash
python build_exe.py
```

### 2. Distribution Package Contents
Include in your distribution:
- The executable file
- `README.md` with setup instructions
- `DISTRIBUTION.md` (this file)
- Any required DLLs or dependencies

### 3. User Setup Instructions
Provide users with:
1. Download and extract the application
2. Run the executable
3. Click "Setup" in the authentication widget
4. Follow the Google API setup instructions
5. Start using the app

## Security Considerations

### Credential Storage
- Credentials are stored in the `private/` folder
- Files are protected with appropriate permissions
- Credentials are not transmitted or shared

### OAuth2 Security
- Uses standard OAuth2 flow
- No credentials are hardcoded in the application
- Each user authenticates with their own Google account

## Troubleshooting

### Common Issues:
1. **"Verification Required"**: Users need to add their email as a test user in Google Cloud Console
2. **"Invalid Client ID"**: Check that the client ID ends with `.apps.googleusercontent.com`
3. **"API Not Enabled"**: Ensure YouTube Data API v3 is enabled in the Google Cloud project

### Support:
- Users should refer to Google's OAuth2 documentation
- Provide links to Google Cloud Console setup guides
- Consider creating a video tutorial for the setup process

## Legal and Compliance

### Terms of Service
- Users must comply with YouTube's Terms of Service
- Users are responsible for their own API usage
- The application is provided "as is"

### Privacy
- No user data is collected or transmitted
- All operations happen locally on the user's machine
- Google authentication is handled directly by Google's servers

## Future Enhancements

### Potential Improvements:
1. **Centralized Configuration**: Web-based credential management
2. **Organization Support**: Multi-tenant authentication
3. **API Key Management**: Rotating credentials and quota monitoring
4. **Audit Logging**: Track upload history and API usage
5. **Bulk Operations**: Support for multiple channel management
