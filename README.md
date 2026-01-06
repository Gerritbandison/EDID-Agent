# Device Inventory Management System

A full-stack enterprise device inventory management system that collects and tracks laptop/computer hardware information and connected monitor EDID data across your organization.

## Features

### Backend API (Python/Flask)
- RESTful API for device and monitor data management
- SQLite (development) / PostgreSQL (production) database support
- JWT-based authentication for web interface
- API key authentication for agents
- Comprehensive EDID parsing for monitor data

### Frontend Web Interface (React + TypeScript)
- Modern dashboard with real-time statistics
- Device inventory with search, filter, and sort
- Monitor inventory with age tracking
- User-centric views with asset grouping
- CSV export functionality
- Dark/light theme support
- Fully responsive design

### Cross-Platform Agent (Python)
- Runs on Windows, macOS, and Linux
- Collects hardware specs (CPU, RAM, storage)
- Parses EDID data from connected monitors
- Automatic check-in with configurable interval
- Retry logic with exponential backoff
- Service/daemon support for background operation

## Quick Start

### Using Docker (Recommended)

1. Clone the repository:
```bash
git clone https://github.com/your-org/EDID-Agent.git
cd EDID-Agent
```

2. Create environment file:
```bash
cp docker/.env.example docker/.env
# Edit docker/.env with your settings
```

3. Start the services:
```bash
cd docker
docker-compose up -d
```

4. Access the web interface at `http://localhost:3000`

### Manual Setup

#### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Initialize database
flask init-db

# Create admin user
flask create-admin

# Generate API key for agents
flask generate-api-key

# Run development server
python run.py
```

#### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Project Structure

```
EDID-Agent/
├── backend/                 # Flask API server
│   ├── app/
│   │   ├── models/         # Database models
│   │   ├── routes/         # API endpoints
│   │   └── utils/          # Helper utilities
│   ├── requirements.txt
│   └── run.py
├── frontend/               # React web interface
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── services/       # API client
│   │   └── types/          # TypeScript types
│   └── package.json
├── agent/                  # Cross-platform agent
│   ├── src/
│   │   ├── collectors/     # Platform-specific collectors
│   │   └── utils/          # EDID parser, helpers
│   ├── installers/         # Platform installers
│   └── config/
├── docker/                 # Docker configuration
│   ├── docker-compose.yml
│   ├── Dockerfile.backend
│   └── Dockerfile.frontend
└── docs/                   # Documentation
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check |
| `/api/devices` | GET | List all devices |
| `/api/devices` | POST | Submit device data (agent) |
| `/api/devices/<id>` | GET | Get device details |
| `/api/monitors` | GET | List all monitors |
| `/api/monitors` | POST | Submit monitor data (agent) |
| `/api/monitors/<id>` | GET | Get monitor details |
| `/api/inventory` | GET | Get full inventory |
| `/api/inventory/stats` | GET | Get dashboard statistics |
| `/api/inventory/export` | GET | Export inventory to CSV |
| `/api/users` | GET | List users with devices |
| `/api/users/<username>` | GET | Get user's devices |
| `/api/auth/login` | POST | User login |
| `/api/auth/register` | POST | Register new user |

## Agent Installation

### Windows

1. Run PowerShell as Administrator:
```powershell
.\agent\installers\windows\install.ps1 -ApiUrl "https://inventory.company.com" -ApiKey "your-api-key"
```

2. For Intune deployment, package the agent with the `intune_install.ps1` script.

### macOS

```bash
sudo ./agent/installers/macos/install.sh
```

### Linux

```bash
sudo ./agent/installers/linux/install.sh
```

## Agent Configuration

The agent can be configured via:

1. **Configuration file** (`config.json`):
```json
{
  "api_url": "https://inventory.company.com",
  "api_key": "your-api-key",
  "check_in_interval": 1800
}
```

2. **Environment variables**:
- `INVENTORY_API_URL`
- `INVENTORY_API_KEY`
- `INVENTORY_CHECK_IN_INTERVAL`

## EDID Parsing

The agent parses EDID (Extended Display Identification Data) from connected monitors to extract:

- Manufacturer ID and name
- Model name and product code
- Serial number
- Manufacture date (week/year)
- Native resolution
- Physical screen dimensions
- Supported resolutions
- Connection type (HDMI, DisplayPort, etc.)

## Security

- All API endpoints require authentication
- Agent uses API keys for secure communication
- Web interface uses JWT tokens
- Passwords are hashed with bcrypt
- CORS is configured for security
- Rate limiting on API endpoints

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | Database connection string | SQLite |
| `SECRET_KEY` | Flask secret key | dev-key |
| `JWT_SECRET_KEY` | JWT signing key | dev-key |
| `API_KEY` | Agent authentication key | default |
| `FLASK_ENV` | Environment (development/production) | development |

## Development

### Running Tests

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

### Building for Production

```bash
# Backend
cd backend
pip install gunicorn
gunicorn --bind 0.0.0.0:5000 run:app

# Frontend
cd frontend
npm run build
```

## Deployment

### Docker Production Deployment

```bash
cd docker
docker-compose --profile production up -d
```

### Intune Deployment

1. Package the agent with required files
2. Use `intune_install.ps1` as the install script
3. Use `intune_detection.ps1` as the detection script
4. Deploy as Win32 app

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT License - see LICENSE file for details
