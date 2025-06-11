# The 5HC Fitness Assessment System

A comprehensive fitness assessment application built with Django for trainers to evaluate, track, and manage their clients' fitness levels. The system features standardized tests, automated scoring, personalized recommendations, professional PDF reports, and a RESTful API.

## Key Features

- 🔐 **Django Authentication**: Secure login system with rate limiting and account lockout
- 🌐 **Modern Web Stack**: Django 5.0.1 with HTMX, Alpine.js, and Tailwind CSS
- 📱 **RESTful API**: Complete API with JWT authentication for mobile/external integrations
- 🧪 **Comprehensive Testing**: pytest-based test suite with 72%+ coverage
- 📊 **Real-time Analytics**: Interactive dashboard with Chart.js visualizations
- 🇰🇷 **Korean Localization**: Full Korean language support with 135+ translations
- 💰 **Financial Management**: Automatic VAT (10%) and card fee (3.5%) calculations
- 📈 **Session Management**: Package-based credit system with payment tracking
- 📄 **PDF Reports**: Professional assessment reports with WeasyPrint
- 🎯 **7 Fitness Tests**: Comprehensive assessment system with age/gender-specific scoring

## Features

### Core Features
- **User Authentication**: Django authentication with custom User model, rate limiting, and remember me functionality
- **Client Management**: Full CRUD operations with search, filtering, and CSV export
- **Fitness Assessment System**: 7 standardized fitness tests:
  - Overhead Squat (lower body function)
  - Push-up Test (upper body function)
  - Single Leg Balance (balance and coordination)
  - Toe Touch (lower body flexibility)
  - FMS Shoulder Mobility (upper body flexibility)
  - Farmer's Carry (grip strength and endurance)
  - Harvard 3-min Step Test (cardiovascular fitness)
- **Automated Scoring**: Age and gender-specific scoring with real-time calculations
- **PDF Reports**: Professional assessment reports with charts and recommendations
- **Session Management**: Package-based credit system with calendar view
- **Financial Tracking**: VAT and card fee calculations with payment history
- **Analytics Dashboard**: Real-time metrics, revenue tracking, and activity feeds

### Technical Features
- **RESTful API**: Complete API with JWT authentication and OpenAPI documentation
- **Real-time UI**: HTMX-powered dynamic updates without page refreshes
- **Responsive Design**: Mobile-friendly interface with Tailwind CSS
- **Korean Support**: Full i18n with Korean translations
- **Testing Suite**: pytest-based tests with factories and fixtures
- **Production Ready**: Configured for Heroku deployment with PostgreSQL

## Project Structure

```
The5HC/
├── README.md                    # This file
├── requirements.txt             # Points to Django requirements
├── Procfile                     # Heroku deployment configuration
├── .gitignore                   # Git ignore file
├── runtime.txt                  # Python version for Heroku
├── django_migration/            # Main Django project
│   ├── apps/                    # Django applications
│   │   ├── accounts/           # User authentication
│   │   ├── analytics/          # Analytics dashboard
│   │   ├── api/                # RESTful API
│   │   ├── assessments/        # Fitness assessments
│   │   ├── clients/            # Client management
│   │   ├── reports/            # PDF generation
│   │   └── sessions/           # Session/payment tracking
│   ├── the5hc/                 # Django settings
│   ├── templates/              # HTML templates
│   ├── static/                 # CSS, JS, fonts
│   ├── locale/                 # Korean translations
│   ├── manage.py               # Django CLI
│   └── requirements.txt        # Python dependencies
├── docs/                       # Documentation
│   ├── kb/                     # Knowledge base
│   └── project/                # Project guidelines
└── logs/                       # Development logs
```

## Requirements

- Python 3.10+
- Django 5.0.1
- PostgreSQL (production) or SQLite (development)
- Redis (optional, for caching)
- System dependencies for WeasyPrint (PDF generation)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/your-username/the5hc.git
cd the5hc/django_migration
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up the database:
```bash
python manage.py migrate
python manage.py compilemessages  # Compile Korean translations
```

5. Create a superuser:
```bash
python manage.py createsuperuser
```

6. Install system dependencies for PDF generation (macOS):
```bash
brew install cairo pango gdk-pixbuf libffi
```

## Usage

1. Start the development server:
```bash
python manage.py runserver
```

2. Access the application at `http://localhost:8000`

3. Login with your superuser credentials or register a new trainer account

4. Navigate through the application:
   - **대시보드**: Analytics dashboard with metrics and charts
   - **회원 관리**: Client management with search and filters
   - **새 평가**: Conduct fitness assessments
   - **세션 관리**: Manage training sessions and payments
   - **보고서**: View and download PDF reports

## API Documentation

### Authentication
```bash
# Get JWT token
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "your_username", "password": "your_password"}'
```

### API Endpoints
- `/api/v1/auth/login/` - JWT authentication
- `/api/v1/clients/` - Client management
- `/api/v1/assessments/` - Assessment CRUD
- `/api/v1/packages/` - Session packages
- `/api/v1/sessions/` - Training sessions
- `/api/v1/payments/` - Payment records
- `/api/v1/users/` - User profiles
- `/api/v1/docs/` - Interactive API documentation (Swagger/ReDoc)

## Testing

### Run all tests:
```bash
pytest
```

### Run with coverage:
```bash
pytest --cov=apps --cov-report=html
```

### Run specific test module:
```bash
pytest apps/accounts/test_models_simple.py -v
```

### API tests:
```bash
python run_api_tests.py  # Interactive test runner
```

## Production Deployment

### Heroku Deployment

1. Create Heroku app:
```bash
heroku create your-app-name
heroku addons:create heroku-postgresql:mini
```

2. Configure environment variables:
```bash
heroku config:set SECRET_KEY='your-secret-key'
heroku config:set DEBUG=False
heroku config:set ALLOWED_HOSTS='your-app-name.herokuapp.com'
```

3. Deploy:
```bash
git push heroku main
heroku run python manage.py migrate
heroku run python manage.py createsuperuser
```

### Environment Variables

- `SECRET_KEY` - Django secret key
- `DEBUG` - Set to False in production
- `DATABASE_URL` - PostgreSQL connection string (auto-set by Heroku)
- `ALLOWED_HOSTS` - Your domain name
- `REDIS_URL` - Redis connection (optional)

## Development Guidelines

### Code Style
- Follow PEP 8 Python style guide
- Use type hints for function parameters and returns
- Write docstrings for all classes and functions
- Keep functions focused and under 50 lines

### Testing Requirements
- Write tests for all new features
- Maintain 70%+ test coverage
- Use factories for test data creation
- Test both success and error cases

### Git Workflow
- Create feature branches for new work
- Write clear commit messages
- Create pull requests for review
- Run tests before merging

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Run the test suite
5. Submit a pull request

## License

This project is proprietary software. All rights reserved.

## Support

For issues or questions:
- Create an issue on GitHub
- Contact the development team
- Check the documentation in `/docs`

