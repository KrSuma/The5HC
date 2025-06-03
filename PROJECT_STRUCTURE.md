# Project Structure

## Overview
The Fitness Assessment System is organized into a clean, modular structure for easy maintenance and deployment.

```
The5HC/
├── main.py                    # Main application entry point
├── Procfile                   # Heroku deployment configuration
├── runtime.txt               # Python version for Heroku
├── requirements.txt          # Python dependencies
├── .gitignore               # Git ignore rules
├── .streamlit/              # Streamlit configuration
│   └── config.toml
│
├── config/                  # Configuration files
│   ├── settings.py         # Main application settings
│   ├── config_production.py # Production-specific settings
│   └── settings_old.py     # Legacy configuration (to be removed)
│
├── src/                    # Source code
│   ├── core/              # Core business logic
│   │   ├── models.py      # Data models
│   │   ├── scoring.py     # Assessment scoring logic
│   │   ├── recommendations.py # AI recommendations
│   │   └── constants.py   # Application constants
│   │
│   ├── data/              # Data layer
│   │   ├── database.py    # Database operations
│   │   ├── database_config.py # Database configuration
│   │   ├── migrate_database.py # Migration scripts
│   │   ├── repositories.py # Repository pattern
│   │   └── cache.py       # Caching logic
│   │
│   ├── services/          # Business services
│   │   ├── service_layer.py # Main service layer
│   │   ├── auth.py        # Authentication service
│   │   ├── auth_service.py # Auth business logic
│   │   ├── client_service.py # Client management
│   │   ├── assessment_service.py # Assessment logic
│   │   ├── report_service.py # Report generation
│   │   ├── session_service.py # Session management
│   │   └── add_client.py  # Client addition helpers
│   │
│   ├── ui/                # User interface
│   │   ├── pages/         # Streamlit pages
│   │   │   ├── ui_pages.py # Main UI pages
│   │   │   ├── assessment_page.py # Assessment form
│   │   │   ├── dashboard.py # Dashboard page
│   │   │   └── login.py   # Login page
│   │   └── components/    # Reusable UI components
│   │       ├── charts.py  # Chart components
│   │       └── forms.py   # Form components
│   │
│   └── utils/             # Utility functions
│       ├── app_logging.py # Logging configuration
│       ├── cache.py       # Cache utilities
│       ├── helpers.py     # Helper functions
│       ├── validators.py  # Input validators
│       ├── pdf_generator.py # PDF generation
│       ├── html_report_generator.py # HTML reports
│       └── weasyprint_pdf_generator.py # WeasyPrint PDFs
│
├── tests/                 # Test files
│   ├── test_deployment.py # Deployment tests
│   └── test_session_management.py # Session tests
│
├── deployment/            # Deployment documentation
│   ├── DEPLOYMENT.md     # Deployment guide
│   └── DEPLOYMENT_CHECKLIST.md # Pre-deployment checklist
│
├── assets/               # Static assets
│   ├── fonts/           # Font files
│   └── images/          # Image files
│
├── data/                # Local data (not in git)
│   ├── fitness_assessment.db # SQLite database
│   └── backups/         # Database backups
│
└── logs/                # Application logs
```

## Key Design Decisions

### 1. **Modular Architecture**
- **Core**: Business logic separated from infrastructure
- **Data**: Database operations isolated in data layer
- **Services**: Business services handle complex operations
- **UI**: Clean separation of presentation logic
- **Utils**: Reusable utilities and helpers

### 2. **Deployment Ready**
- Heroku files (`Procfile`, `runtime.txt`) in root
- Database abstraction for SQLite (dev) and PostgreSQL (prod)
- Environment-based configuration

### 3. **Security**
- Authentication separated into service layer
- Password hashing with bcrypt
- Session management
- Input validation and sanitization

### 4. **Scalability**
- Repository pattern for data access
- Service layer for business logic
- Caching layer for performance
- Modular structure for easy extension

## Import Structure

```python
# Main application
from src.services.service_layer import AuthService, ClientService
from src.ui.pages.ui_pages import dashboard_page
from config.settings import config

# Core business logic
from src.core.scoring import calculate_score
from src.core.recommendations import get_recommendations

# Data operations
from src.data.database import get_db_connection
from src.data.repositories import ClientRepository

# Utilities
from src.utils.pdf_generator import create_pdf
from src.utils.app_logging import logger
```

## Development Workflow

1. **Local Development**: Uses SQLite database in `data/` directory
2. **Testing**: Run tests from `tests/` directory
3. **Deployment**: Push to Heroku, automatically uses PostgreSQL
4. **Configuration**: Environment-based settings in `config/`

## Next Steps

1. Remove legacy files (`settings_old.py`)
2. Add comprehensive tests
3. Implement CI/CD pipeline
4. Add API documentation
5. Implement backup strategies