# AI Cycling Coach - Terminal Edition

🚴‍♂️ An intelligent cycling training coach with a sleek Terminal User Interface (TUI) that creates personalized training plans and analyzes your workouts using AI, with seamless Garmin Connect integration.

## ✨ Features

- **🧠 AI-Powered Plan Generation**: Create personalized 4-week training plans based on your goals and constraints
- **📊 Automatic Workout Analysis**: Get detailed AI feedback on your completed rides with terminal-based visualizations
- **⌚ Garmin Connect Integration**: Sync activities automatically from your Garmin device
- **🔄 Plan Evolution**: Training plans adapt based on your actual performance
- **🗺️ GPX Route Management**: Upload and visualize your favorite cycling routes with ASCII maps
- **📈 Progress Tracking**: Monitor your training progress with terminal charts and metrics
- **💻 Pure Terminal Interface**: Beautiful, responsive TUI that works entirely in your terminal
- **🗃️ SQLite Database**: Lightweight, portable database that travels with your data
- **🚀 No Docker Required**: Simple installation and native performance

## 🏁 Quick Start

### Option 1: Automated Installation (Recommended)
```bash
git clone https://github.com/ai-cycling-coach/ai-cycling-coach.git
cd ai-cycling-coach
./install.sh
```

### Option 2: Manual Installation
```bash
# Clone and setup
git clone https://github.com/ai-cycling-coach/ai-cycling-coach.git
cd ai-cycling-coach

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install
pip install -e .

# Initialize database
make init-db

# Run the application
cycling-coach
```

## ⚙️ Configuration

Edit the `.env` file with your settings:

```bash
# Database Configuration (SQLite)
DATABASE_URL=sqlite+aiosqlite:///data/cycling_coach.db

# File Storage
GPX_STORAGE_PATH=data/gpx

# AI Service Configuration  
OPENROUTER_API_KEY=your_openrouter_api_key_here
AI_MODEL=deepseek/deepseek-r1

# Garmin Connect Credentials
GARMIN_USERNAME=your_garmin_email@example.com
GARMIN_PASSWORD=your_secure_password

# Optional: Logging Configuration
LOG_LEVEL=INFO
```

## 🎮 Usage

### Terminal Interface

Start the application with:
```bash
cycling-coach
# or
ai-cycling-coach
# or
python main.py
```

Navigate through the interface using:

1. **🏠 Dashboard**: View recent workouts, weekly stats, and sync status
2. **📋 Plans**: Generate new training plans or manage existing ones  
3. **💪 Workouts**: Sync from Garmin, view detailed analysis, and approve AI suggestions
4. **📏 Rules**: Define custom training constraints and preferences
5. **🗺️ Routes**: Upload GPX files and view ASCII route visualizations

### Key Features

#### 🧠 AI-Powered Analysis
- Detailed workout feedback with actionable insights
- Performance trend analysis
- Training load recommendations
- Recovery suggestions

#### 🗺️ ASCII Route Visualization
```
Route Map:
S●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●E
●                                                   ●
●          Morning Loop - 15.2km                    ●
●                                                   ●
●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●

Elevation Profile (50m - 180m):
████████████████████████████████████████████████████████████
██████████████████████████████  ████████████████████████████
███████████████████████████        ████████████████████████
███████████████████████              ██████████████████████
```

#### 📊 Terminal-Based Charts
- Heart rate zones
- Power distribution  
- Training load trends
- Weekly volume tracking

## 🏗️ Architecture

### 🔧 Technology Stack
- **Backend**: Python with SQLAlchemy + SQLite
- **TUI Framework**: Textual (Rich terminal interface)
- **AI Integration**: OpenRouter API (Deepseek R1, Claude, GPT)
- **Garmin Integration**: garth library
- **Database**: SQLite with async support

### 📁 Project Structure
```
ai-cycling-coach/
├── main.py                 # Application entrypoint
├── backend/               # Core business logic
│   ├── app/
│   │   ├── models/       # Database models
│   │   ├── services/     # Business services  
│   │   └── config.py     # Configuration
│   └── alembic/          # Database migrations
├── tui/                  # Terminal interface
│   ├── views/           # TUI screens
│   ├── services/        # TUI service layer
│   └── widgets/         # Custom UI components
└── data/                # SQLite database and files
    ├── cycling_coach.db
    └── gpx/            # GPX route files
```

## 🛠️ Development

### Setup Development Environment
```bash
# Clone repository
git clone https://github.com/ai-cycling-coach/ai-cycling-coach.git
cd ai-cycling-coach

# Install in development mode
make dev-install

# Initialize database
make init-db

# Run tests
make test

# Format code
make format

# Run application
make run
```

### Available Make Commands
```bash
make help          # Show all available commands
make install       # Install the application
make dev-install   # Install in development mode
make run           # Run the application
make init-db       # Initialize the database
make test          # Run tests
make clean         # Clean build artifacts
make build         # Build distribution packages
make package       # Create standalone executable
make setup         # Complete setup for new users
```

### Creating a Standalone Executable
```bash
make package
# Creates: dist/cycling-coach
```

## 🚀 Deployment Options

### 1. Portable Installation
```bash
# Create portable package
make build
pip install dist/ai-cycling-coach-*.whl
```

### 2. Standalone Executable
```bash
# Create single-file executable
make package
# Copy dist/cycling-coach to target system
```

### 3. Development Installation
```bash
# For development and testing
make dev-install
```

## 📋 Requirements

- **Python**: 3.8 or higher
- **Operating System**: Linux, macOS, Windows
- **Terminal**: Any terminal with Unicode support
- **Memory**: ~100MB RAM
- **Storage**: ~50MB + data files

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`make test`)
5. Format code (`make format`)
6. Commit changes (`git commit -m 'Add amazing feature'`)
7. Push to branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## 🐛 Troubleshooting

### Common Issues

**Database errors:**
```bash
make init-db  # Reinitialize database
```

**Import errors:**
```bash
pip install -e .  # Reinstall in development mode
```

**Garmin sync fails:**
- Check credentials in `.env`
- Verify Garmin Connect account access
- Check internet connection

**TUI rendering issues:**
- Ensure terminal supports Unicode
- Try different terminal emulators
- Check terminal size (minimum 80x24)

### Getting Help

- 📖 Check the documentation
- 🐛 Open an issue on GitHub  
- 💬 Join our community discussions

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Textual](https://github.com/Textualize/textual) - Amazing TUI framework
- [garth](https://github.com/matin/garth) - Garmin Connect integration
- [OpenRouter](https://openrouter.ai/) - AI model access
- [SQLAlchemy](https://www.sqlalchemy.org/) - Database toolkit