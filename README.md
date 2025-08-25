# Media Uploader for YouTube 🎬

A modern, feature-rich desktop application for uploading media files to YouTube with a beautiful dark theme and intuitive interface.

## ✨ Features

- **🎯 Modern Dark Theme** - Discord + Monokai inspired design with glass morphism effects
- **🔐 Google Authentication** - Secure OAuth2 login with persistent sessions
- **📤 Real YouTube Uploads** - Direct integration with YouTube Data API v3
- **🎵 Multi-Format Support** - Upload MP4, MP3, and other media formats
- **⚡ Batch Uploads** - Upload multiple files simultaneously
- **📊 Progress Tracking** - Real-time upload progress with speed and ETA
- **🎨 Subtle Animations** - Smooth fade-in, shake, and pulse effects
- **🔍 Media Preview** - Preview videos and audio before upload
- **📝 Metadata Editing** - Edit titles and descriptions for each upload
- **🔄 Persistent Login** - Stay logged in across application restarts
- **🛡️ Security** - Secure credential storage and validation
- **📱 Responsive Design** - Adapts to different screen sizes

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- Google account for YouTube uploads
- Google Cloud Project with YouTube Data API enabled

### Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd media_uploader
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up Google authentication:**
   - Follow the [Setup Guide](SETUP_GUIDE.md) to configure Google OAuth2
   - Place your `client_secret.json` in the `private/` folder

4. **Run the application:**
   ```bash
   python -m app.main
   ```

## 📖 Usage

### First Time Setup

1. **Authentication Setup:**
   - Click the "ℹ️" button in the auth widget to check setup status
   - If setup is required, follow the instructions to configure Google OAuth2
   - See [SETUP_GUIDE.md](SETUP_GUIDE.md) for detailed instructions

2. **Login:**
   - Click "🔑 Login with Google" to authenticate
   - Grant permissions when prompted in your browser
   - You'll see "✅ Logged in as [your-email]" when successful

### Uploading Media

1. **Select Media:**
   - Click "📁 Choose Folder" or "🔍 Scan Current Folder"
   - The app will find MP4, MP3, and other media files

2. **Edit Metadata:**
   - Fill in title and description for each file
   - Preview media using the play button

3. **Upload:**
   - Select files using the checkboxes
   - Click "🚀 Upload Selected" for batch uploads
   - Or click individual "📤 Upload to YouTube" buttons

4. **Monitor Progress:**
   - Watch real-time progress with speed and ETA
   - View batch upload summary
   - Check individual file status

## 🏗️ Architecture

```
media_uploader/
├── app/                    # Application UI components
│   ├── ui/                # User interface modules
│   │   ├── main_window.py # Main application window
│   │   ├── media_row.py   # Individual media item display
│   │   ├── auth_widget.py # Google authentication widget
│   │   ├── upload_status.py # Upload progress display
│   │   └── upload_summary.py # Batch upload summary
├── core/                   # Core functionality
│   ├── auth_manager.py    # Google OAuth2 authentication
│   ├── styles.py          # UI styling and theming
│   ├── animations.py      # UI animation helpers
│   ├── models.py          # Data models and enums
│   ├── validators.py      # Input validation
│   ├── upload_manager.py  # YouTube upload management
│   └── file_organizer.py  # File organization utilities
├── services/              # External service integrations
│   └── youtube_service.py # YouTube Data API integration
├── infra/                 # Infrastructure components
│   ├── events.py          # Event system
│   └── uploader.py        # Upload worker threads
└── tests/                 # Unit tests
```

## 🧪 Testing

Run the test suite:

```bash
# Run all tests
python run_tests.py

# Run linting
python run_lint.py

# Run specific test categories
pytest tests/ -m unit
pytest tests/ -m integration
```

## 📦 Building

### Development Build

```bash
# Install build dependencies
pip install -r requirements-build.txt

# Run the application
python -m app.main
```

### Production Build

```bash
# Build standalone executable
python build.py

# The executable will be created in dist/MediaUploader.exe
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Set up pre-commit hooks
pre-commit install

# Run tests and linting
python run_tests.py
python run_lint.py
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- 📖 [Setup Guide](SETUP_GUIDE.md) - Initial setup and configuration
- 🧪 [Testing Guide](TESTING_GUIDE.md) - Running tests and debugging
- 🏗️ [Build Guide](BUILD_GUIDE.md) - Building and distribution
- 🔧 [Integration Guide](INTEGRATION_GUIDE.md) - API integration details
- 📋 [Linting Guide](LINTING_GUIDE.md) - Code quality and style

## ⚠️ Important Notes

- **Authentication Required**: You need a Google Cloud Project with YouTube Data API enabled
- **Client Secret**: Place your `client_secret.json` in the `private/` folder (not tracked by git)
- **Rate Limits**: YouTube API has rate limits - batch uploads may be throttled
- **File Formats**: Supports MP4, MP3, and other formats supported by YouTube

## 🎯 Roadmap

- [ ] Enhanced video preview with thumbnails
- [ ] Scheduled uploads
- [ ] Playlist management
- [ ] Advanced metadata editing
- [ ] Upload templates
- [ ] Multi-language support
