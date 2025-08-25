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
   python main.py
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
│   └── scanner.py         # Media file discovery
├── services/              # External service integrations
│   └── youtube_service.py # YouTube API integration
├── infra/                 # Infrastructure components
│   ├── uploader.py        # Upload threading and management
│   └── events.py          # Event system
├── private/               # Private configuration (gitignored)
│   └── client_secret.json # Google OAuth2 credentials
└── main.py               # Application entry point
```

## 🎨 Design System

### Color Palette
- **Primary**: Discord Blue (#5865f2)
- **Accent**: Monokai Pink (#f92672)
- **Background**: Dark gradients with glass morphism
- **Text**: High contrast with proper hierarchy
- **Status**: Semantic colors (success, warning, error)

### Animations
- **Fade-in**: Smooth appearance of new elements
- **Shake**: Error feedback for validation failures
- **Pulse**: Loading states and attention indicators
- **Slide**: Smooth transitions between states

### Glass Morphism
- Semi-transparent backgrounds
- Subtle borders and shadows
- Blur effects for depth
- Gradient overlays for visual interest

## 🔐 Authentication System

### Features
- **OAuth2 Flow**: Secure Google authentication
- **Persistent Sessions**: Stay logged in across app restarts
- **Automatic Refresh**: Tokens refresh automatically when needed
- **Setup Validation**: Comprehensive setup checking
- **Error Handling**: Detailed error messages and recovery

### Security
- **Secure Storage**: Credentials stored with proper permissions
- **Validation**: Client secret and credential validation
- **Error Recovery**: Graceful handling of authentication failures
- **Logout**: Complete credential cleanup on logout

## 📤 Upload Process Feedback

### Individual Upload Status
- **Icons**: Visual status indicators (⏳, 📤, ✅, ❌)
- **Messages**: Clear status descriptions
- **Progress**: Real-time upload progress
- **Metrics**: Speed and ETA calculations
- **Colors**: Semantic color coding

### Batch Upload Summary
- **Progress Bar**: Overall batch progress
- **Live Counters**: Success/failure counts
- **Status Updates**: Current batch status
- **Completion Summary**: Final results display
- **Auto-hide**: Automatic cleanup after completion

## ⚙️ Configuration

### Environment Variables
```bash
# Optional: Custom client secret path
GOOGLE_CLIENT_SECRET_PATH=path/to/client_secret.json
```

### File Structure
```
private/
├── client_secret.json    # Google OAuth2 credentials
├── token.pickle         # Stored authentication tokens
└── auth_state.json      # Authentication state
```

## 🛠️ Development

### Running in Development
```bash
# Install development dependencies
pip install -r requirements.txt

# Run with debug logging
python main.py --debug

# Run demo with sample files
python demo.py
```

### Code Style
- Follow PEP 8 guidelines
- Use type hints throughout
- Keep functions small and focused
- Document all public APIs

### Testing
```bash
# Run tests (when implemented)
pytest

# Run linting
black .
mypy .
```

## 🐛 Troubleshooting

### Common Issues

**Authentication Problems:**
- Check `client_secret.json` is in `private/` folder
- Verify YouTube Data API v3 is enabled
- Ensure OAuth consent screen is configured
- Check quota limits in Google Cloud Console

**Upload Failures:**
- Verify file format is supported
- Check file size limits (128GB max)
- Ensure stable internet connection
- Check YouTube API quota

**UI Issues:**
- Update PySide6 to latest version
- Check display scaling settings
- Verify graphics drivers are current

### Logs
Application logs are written to:
- Console output (development)
- `media_uploader.log` (production)

## 📋 Requirements

### Core Dependencies
- **PySide6**: Modern Qt-based GUI framework
- **google-auth**: Google OAuth2 authentication
- **google-api-python-client**: YouTube Data API integration
- **PyJWT**: JWT token handling

### System Requirements
- **OS**: Windows 10+, macOS 10.14+, Linux
- **Python**: 3.8 or higher
- **Memory**: 512MB RAM minimum
- **Storage**: 100MB free space
- **Network**: Internet connection for uploads

## 🧪 Development

### Code Quality

The project uses comprehensive linting and testing tools to maintain code quality:

#### Linting Tools
- **Black**: Code formatter for consistent Python formatting
- **isort**: Import sorter for organized imports  
- **Flake8**: Style guide enforcement and error detection
- **MyPy**: Static type checking
- **Bandit**: Security vulnerability detection

#### Quick Linting Commands
```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run all linters
python run_lint.py --all

# Check formatting without changes
python run_lint.py --all --check

# Run specific linter
python run_lint.py --black
python run_lint.py --flake8
python run_lint.py --mypy
```

#### Pre-commit Hooks
```bash
# Install pre-commit hooks
pre-commit install

# Run on all files
pre-commit run --all-files
```

For detailed linting information, see [LINTING_GUIDE.md](LINTING_GUIDE.md).

### Testing

The project includes comprehensive unit tests:

```bash
# Run all tests
python run_tests.py --type all

# Run specific test types
python run_tests.py --type unit
python run_tests.py --type integration

# Run with coverage
python run_tests.py --type coverage
```

For detailed testing information, see [TESTING_GUIDE.md](TESTING_GUIDE.md).

## 🔄 Roadmap

### Planned Features
- [ ] **Playlist Support**: Create and manage YouTube playlists
- [ ] **Thumbnail Generation**: Automatic thumbnail creation
- [ ] **Scheduled Uploads**: Upload at specific times
- [ ] **Advanced Metadata**: Tags, categories, privacy settings
- [ ] **Upload History**: Track and manage past uploads
- [ ] **Multi-Account**: Support for multiple YouTube accounts
- [ ] **Drag & Drop**: Drag files directly into the application
- [ ] **Keyboard Shortcuts**: Power user shortcuts
- [ ] **Export/Import**: Backup and restore settings
- [ ] **Plugin System**: Extensible architecture

### Technical Improvements
- [x] **Unit Tests**: Comprehensive test coverage
- [x] **Code Quality**: Linting and type checking
- [ ] **CI/CD**: Automated testing and deployment
- [ ] **Performance**: Optimize for large file uploads
- [ ] **Accessibility**: Screen reader and keyboard navigation
- [ ] **Internationalization**: Multi-language support
- [ ] **Auto-updates**: Automatic application updates

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines
- Follow the existing code style
- Add tests for new features
- Update documentation as needed
- Ensure all tests pass before submitting

## 📞 Support

### Getting Help
- Check the [Troubleshooting](#troubleshooting) section
- Review the [Setup Guide](SETUP_GUIDE.md)
- Search existing issues on GitHub
- Create a new issue with detailed information

### Bug Reports
When reporting bugs, please include:
- Operating system and version
- Python version
- Application version
- Steps to reproduce
- Error messages and logs
- Expected vs actual behavior

## 🙏 Acknowledgments

- **Google**: YouTube Data API and OAuth2
- **Qt/PySide6**: GUI framework
- **Discord**: UI design inspiration
- **Monokai**: Color scheme inspiration
- **Open Source Community**: Various libraries and tools

---

**Made with ❤️ for content creators everywhere**
