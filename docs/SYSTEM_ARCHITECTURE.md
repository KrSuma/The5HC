# The5HC Fitness Assessment System - Architecture Reference

## Table of Contents
1. [System Overview](#system-overview)
2. [Architecture Pattern](#architecture-pattern)
3. [Core Domain Models](#core-domain-models)
4. [Service Layer](#service-layer)
5. [Database Schema](#database-schema)
6. [UI Components](#ui-components)
7. [Authentication & Security](#authentication--security)
8. [Caching Strategy](#caching-strategy)
9. [Key Constants & Configuration](#key-constants--configuration)
10. [Technology Stack](#technology-stack)
11. [API Reference](#api-reference)
12. [Future Feature Planning Guide](#future-feature-planning-guide)

## System Overview

The5HC Fitness Assessment System is a comprehensive web application for conducting and managing physical fitness assessments. Built with Python and Streamlit, it provides:

- Multi-user authentication system for trainers
- Client management with detailed profiles
- 7 standardized fitness tests with scoring
- Progress tracking and analytics
- Session-based training management
- PDF report generation
- Real-time recommendations

### Key Features
- **Secure Authentication**: Rate-limited login with bcrypt hashing
- **Comprehensive Assessment**: 7 fitness tests with age/gender-specific scoring
- **Smart Caching**: Multi-level caching for optimal performance
- **Dual Database Support**: SQLite (dev) and PostgreSQL (production)
- **Session Management**: Credit-based training session tracking with VAT/fee calculations
- **Analytics**: Progress tracking with asymmetry detection
- **Financial Management**: Automatic VAT (10%) and card processing fee (3.5%) calculations
- **Audit Trail**: Comprehensive logging of all financial transactions

## Architecture Pattern

The system follows a **Layered Architecture** with **Service-Oriented Design**:

```
┌─────────────────────────────────────────┐
│         Presentation Layer              │
│        (Streamlit UI Pages)             │
├─────────────────────────────────────────┤
│          Service Layer                  │
│    (Business Logic & Orchestration)     │
├─────────────────────────────────────────┤
│           Domain Layer                  │
│      (Core Models & Business Rules)     │
├─────────────────────────────────────────┤
│        Data Access Layer                │
│    (Repositories & Database Access)     │
├─────────────────────────────────────────┤
│       Infrastructure Layer              │
│      (Utilities & Cross-cutting)        │
└─────────────────────────────────────────┘
```

### Design Patterns Used
- **Repository Pattern**: Abstract data access
- **Service Layer Pattern**: Business logic organization
- **Factory Pattern**: Repository instantiation
- **Unit of Work**: Transaction management
- **Decorator Pattern**: Caching and authentication
- **Strategy Pattern**: Database adapter selection

## Core Domain Models

### BaseEntity (Abstract Base Class)
```python
class BaseEntity:
    id: Optional[int]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
```

### Trainer Model
```python
class Trainer(BaseEntity):
    username: str              # Unique username
    password_hash: str         # Bcrypt hashed password
    email: Optional[str]       # Contact email
    full_name: Optional[str]   # Display name
    is_active: bool = True     # Account status
    last_login: Optional[datetime]
    failed_login_attempts: int = 0
    lockout_until: Optional[datetime]
```

### Client Model
```python
class Client(BaseEntity):
    trainer_id: int            # Foreign key to trainer
    name: str                  # Client full name
    age: int                   # Age in years
    gender: str                # 'male' or 'female'
    height: float              # Height in cm
    weight: float              # Weight in kg
    phone: Optional[str]       # Contact number
    email: Optional[str]       # Contact email
    medical_conditions: Optional[str]
    notes: Optional[str]       # Additional notes
```

### Assessment Model
```python
class Assessment(BaseEntity):
    client_id: int             # Foreign key to client
    trainer_id: int            # Foreign key to trainer
    assessment_date: datetime
    
    # Test Results (all in seconds or reps)
    shoulder_mobility_left: Optional[float]
    shoulder_mobility_right: Optional[float]
    hip_stability_left: Optional[float]
    hip_stability_right: Optional[float]
    neck_rotation_left: Optional[float]
    neck_rotation_right: Optional[float]
    hip_mobility_left: Optional[float]
    hip_mobility_right: Optional[float]
    thoracic_rotation_left: Optional[float]
    thoracic_rotation_right: Optional[float]
    push_up_count: Optional[int]
    farmers_carry_time: Optional[float]
    
    # Compensation Patterns (JSON strings)
    compensations: Optional[Dict[str, List[str]]]
    
    # Calculated Scores
    total_score: Optional[float]
    mobility_score: Optional[float]
    stability_score: Optional[float]
    strength_score: Optional[float]
    
    # Additional Fields
    notes: Optional[str]
    recommendations: Optional[str]
```

## Service Layer

### AuthService
**Purpose**: Handle authentication and user management

```python
class AuthService:
    def register_trainer(username: str, password: str, email: str, full_name: str) -> Tuple[bool, str]
    def login(username: str, password: str) -> Optional[Trainer]
    def logout() -> None
    def get_current_user() -> Optional[Trainer]
    def change_password(trainer_id: int, old_password: str, new_password: str) -> Tuple[bool, str]
```

### ClientService
**Purpose**: Manage client data with caching

```python
class ClientService:
    def create_client(trainer_id: int, client_data: dict) -> Client
    def get_client(client_id: int) -> Optional[Client]
    def get_clients_by_trainer(trainer_id: int) -> List[Client]
    def update_client(client_id: int, updates: dict) -> bool
    def delete_client(client_id: int) -> bool
    def search_clients(trainer_id: int, query: str) -> List[Client]
```

### AssessmentService
**Purpose**: Handle fitness assessments and scoring

```python
class AssessmentService:
    def create_assessment(client_id: int, trainer_id: int, test_data: dict) -> Assessment
    def get_assessment(assessment_id: int) -> Optional[Assessment]
    def get_client_assessments(client_id: int) -> List[Assessment]
    def calculate_scores(assessment: Assessment) -> dict
    def get_latest_assessment(client_id: int) -> Optional[Assessment]
    def get_progress_data(client_id: int) -> dict
```

### DashboardService
**Purpose**: Provide dashboard statistics and metrics

```python
class DashboardService:
    def get_dashboard_stats(trainer_id: int) -> dict
    def get_recent_assessments(trainer_id: int, limit: int = 5) -> List[dict]
    def get_client_distribution(trainer_id: int) -> dict
    def get_performance_trends(trainer_id: int) -> dict
```

### AnalyticsService
**Purpose**: Advanced analytics and insights

```python
class AnalyticsService:
    def get_client_progress(client_id: int) -> dict
    def detect_asymmetries(assessment: Assessment) -> dict
    def get_improvement_areas(assessment: Assessment) -> List[str]
    def generate_insights(client_id: int) -> dict
```

### SessionManagementService
**Purpose**: Training session and credit management with financial calculations

```python
class SessionManagementService:
    def create_package(client_id: int, credits: int, price: float) -> SessionPackage
    def create_package_with_fees(client_id: int, trainer_id: int, gross_amount: int, session_price: int) -> SessionPackage
    def schedule_session(client_id: int, date: datetime, notes: str) -> TrainingSession
    def complete_session(session_id: int) -> bool
    def cancel_session(session_id: int) -> bool
    def get_remaining_credits(client_id: int) -> int
    def get_session_history(client_id: int) -> List[TrainingSession]
    def calculate_fee_breakdown(gross_amount: int) -> dict
    def add_credits_with_fees(package_id: int, gross_amount: int) -> bool
```

## Database Schema

### trainers
```sql
CREATE TABLE trainers (
    id INTEGER PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(100) UNIQUE,
    full_name VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    last_login TIMESTAMP,
    failed_login_attempts INTEGER DEFAULT 0,
    lockout_until TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### clients
```sql
CREATE TABLE clients (
    id INTEGER PRIMARY KEY,
    trainer_id INTEGER NOT NULL,
    name VARCHAR(100) NOT NULL,
    age INTEGER NOT NULL,
    gender VARCHAR(10) NOT NULL,
    height FLOAT NOT NULL,
    weight FLOAT NOT NULL,
    phone VARCHAR(20),
    email VARCHAR(100),
    medical_conditions TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (trainer_id) REFERENCES trainers(id)
);
```

### assessments
```sql
CREATE TABLE assessments (
    id INTEGER PRIMARY KEY,
    client_id INTEGER NOT NULL,
    trainer_id INTEGER NOT NULL,
    assessment_date TIMESTAMP NOT NULL,
    
    -- Test results
    shoulder_mobility_left FLOAT,
    shoulder_mobility_right FLOAT,
    hip_stability_left FLOAT,
    hip_stability_right FLOAT,
    neck_rotation_left FLOAT,
    neck_rotation_right FLOAT,
    hip_mobility_left FLOAT,
    hip_mobility_right FLOAT,
    thoracic_rotation_left FLOAT,
    thoracic_rotation_right FLOAT,
    push_up_count INTEGER,
    farmers_carry_time FLOAT,
    
    -- Compensations (JSON)
    compensations TEXT,
    
    -- Scores
    total_score FLOAT,
    mobility_score FLOAT,
    stability_score FLOAT,
    strength_score FLOAT,
    
    notes TEXT,
    recommendations TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (client_id) REFERENCES clients(id),
    FOREIGN KEY (trainer_id) REFERENCES trainers(id)
);
```

### session_packages
```sql
CREATE TABLE session_packages (
    id INTEGER PRIMARY KEY,
    client_id INTEGER NOT NULL,
    total_credits INTEGER NOT NULL,
    used_credits INTEGER DEFAULT 0,
    price FLOAT NOT NULL,
    purchase_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expiry_date TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- New fee-related columns
    gross_amount INTEGER,
    vat_amount INTEGER,
    card_fee_amount INTEGER,
    net_amount INTEGER,
    vat_rate DECIMAL(5,2) DEFAULT 0.10,
    card_fee_rate DECIMAL(5,2) DEFAULT 0.035,
    fee_calculation_method VARCHAR(20) DEFAULT 'inclusive',
    
    FOREIGN KEY (client_id) REFERENCES clients(id)
);
```

### training_sessions
```sql
CREATE TABLE training_sessions (
    id INTEGER PRIMARY KEY,
    client_id INTEGER NOT NULL,
    package_id INTEGER NOT NULL,
    scheduled_date TIMESTAMP NOT NULL,
    status VARCHAR(20) DEFAULT 'scheduled',
    notes TEXT,
    completed_at TIMESTAMP,
    cancelled_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (client_id) REFERENCES clients(id),
    FOREIGN KEY (package_id) REFERENCES session_packages(id)
);
```

### payment_history
```sql
CREATE TABLE payment_history (
    id INTEGER PRIMARY KEY,
    client_id INTEGER NOT NULL,
    package_id INTEGER NOT NULL,
    amount FLOAT NOT NULL,
    payment_method VARCHAR(50),
    payment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    
    -- New fee-related columns
    gross_amount INTEGER,
    vat_amount INTEGER,
    card_fee_amount INTEGER,
    net_amount INTEGER,
    vat_rate DECIMAL(5,2),
    card_fee_rate DECIMAL(5,2),
    
    FOREIGN KEY (client_id) REFERENCES clients(id),
    FOREIGN KEY (package_id) REFERENCES session_packages(id)
);
```

### fee_audit_log
```sql
CREATE TABLE fee_audit_log (
    id INTEGER PRIMARY KEY,
    package_id INTEGER,
    payment_id INTEGER,
    calculation_type VARCHAR(20), -- 'package_creation', 'credit_addition', 'fee_adjustment'
    gross_amount INTEGER NOT NULL,
    vat_amount INTEGER NOT NULL,
    card_fee_amount INTEGER NOT NULL,
    net_amount INTEGER NOT NULL,
    vat_rate DECIMAL(5,2) NOT NULL,
    card_fee_rate DECIMAL(5,2) NOT NULL,
    calculation_details TEXT, -- JSON with detailed calculation steps
    created_by INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (package_id) REFERENCES session_packages(id),
    FOREIGN KEY (payment_id) REFERENCES payment_history(id),
    FOREIGN KEY (created_by) REFERENCES trainers(id)
);
```

## UI Components

### Main Pages (src/ui/pages/)

#### 1. Login Page
- Username/password authentication
- Registration form for new trainers
- Rate limiting display
- Session timeout handling

#### 2. Dashboard
- Total clients, assessments, active sessions
- Recent assessments table
- Quick search functionality
- Performance charts

#### 3. Client Management
- Client list with search/filter
- Add/Edit client forms
- Client detail view
- Assessment history

#### 4. Assessment Page
- 7 test tabs with input forms
- Real-time score calculation
- Compensation pattern tracking
- Save and generate report buttons

#### 5. Session Management
- Package purchase interface with fee breakdown
- Session scheduling calendar
- Credit tracking with VAT/fee calculations
- Session history
- Real-time fee calculation display
- Payment history with detailed breakdowns

### Chart Components (src/ui/components/charts.py)
- Progress line charts
- Score comparison radar charts
- Asymmetry detection visualizations
- Distribution histograms

## Authentication & Security

### Security Features
1. **Password Security**
   - Bcrypt hashing with 12 rounds
   - Unique salt per password
   - No plain text storage

2. **Rate Limiting**
   - Max 5 failed attempts
   - 30-minute lockout period
   - Per-user tracking

3. **Session Management**
   - Token-based sessions
   - 30-minute timeout
   - Activity tracking
   - CSRF protection

4. **Input Validation**
   - SQL injection prevention
   - XSS protection
   - Input sanitization

### Authentication Flow
```python
@login_required
def protected_function():
    # Decorator ensures user is logged in
    # Redirects to login if not authenticated
    pass
```

## Caching Strategy

### Cache Levels
```python
# Client cache: 10-minute TTL
client_cache = LRUCache(maxsize=1000, ttl=600)

# Assessment cache: 5-minute TTL
assessment_cache = LRUCache(maxsize=500, ttl=300)

# Statistics cache: 1-minute TTL
stats_cache = LRUCache(maxsize=100, ttl=60)

# Trainer cache: 30-minute TTL
trainer_cache = LRUCache(maxsize=50, ttl=1800)
```

### Cache Usage
```python
@cached(cache=client_cache)
def get_client(client_id: int) -> Optional[Client]:
    # Automatic caching with decorator
    pass
```

## Key Constants & Configuration

### Fitness Test Weights
```python
TEST_WEIGHTS = {
    'mobility': {
        'shoulder_mobility': 0.3,
        'neck_rotation': 0.2,
        'hip_mobility': 0.3,
        'thoracic_rotation': 0.2
    },
    'stability': {
        'hip_stability': 1.0  # Single test category
    },
    'strength': {
        'push_up': 0.5,
        'farmers_carry': 0.5
    }
}
```

### Category Weights
```python
CATEGORY_WEIGHTS = {
    'mobility': 0.35,
    'stability': 0.30,
    'strength': 0.35
}
```

### Score Levels
```python
SCORE_LEVELS = {
    (90, 100): "Very Excellent",
    (80, 89): "Excellent",
    (70, 79): "Very Good",
    (60, 69): "Good",
    (50, 59): "Above Average",
    (40, 49): "Average",
    (30, 39): "Below Average",
    (20, 29): "Poor",
    (0, 19): "Needs Improvement"
}
```

### Configuration Settings
```python
# config/settings.py
class Settings:
    # Database
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///fitness_assessment.db')
    
    # Security
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key')
    PASSWORD_SALT_ROUNDS = 12
    MAX_LOGIN_ATTEMPTS = 5
    LOCKOUT_DURATION = 30  # minutes
    
    # Session
    SESSION_TIMEOUT = 30  # minutes
    
    # Caching
    CACHE_TTL = {
        'client': 600,      # 10 minutes
        'assessment': 300,  # 5 minutes
        'stats': 60,        # 1 minute
        'trainer': 1800     # 30 minutes
    }
    
    # PDF Generation
    PDF_PAGE_SIZE = 'A4'
    PDF_MARGIN = '1cm'
```

## Technology Stack

### Core Technologies
- **Language**: Python 3.8+
- **Web Framework**: Streamlit 1.x
- **Databases**: SQLite (dev), PostgreSQL (production)
- **Authentication**: bcrypt
- **PDF Generation**: WeasyPrint
- **Charts**: Matplotlib
- **Deployment**: Heroku

### Key Dependencies
```python
# requirements.txt
streamlit>=1.28.0
bcrypt>=4.0.1
matplotlib>=3.5.0
weasyprint>=52.5
psycopg2-binary>=2.9.0
python-dotenv>=0.19.0
```

## API Reference

### Repository Interface
```python
class Repository(ABC):
    @abstractmethod
    def create(self, entity: T) -> T:
        """Create a new entity"""
        
    @abstractmethod
    def get(self, id: int) -> Optional[T]:
        """Get entity by ID"""
        
    @abstractmethod
    def update(self, id: int, entity: T) -> bool:
        """Update existing entity"""
        
    @abstractmethod
    def delete(self, id: int) -> bool:
        """Delete entity"""
        
    @abstractmethod
    def list(self, **filters) -> List[T]:
        """List entities with optional filters"""
```

### Service Layer Pattern
```python
class ServiceLayer:
    def __init__(self, unit_of_work: UnitOfWork):
        self.uow = unit_of_work
        
    def execute(self, operation):
        with self.uow:
            result = operation()
            self.uow.commit()
            return result
```

## Future Feature Planning Guide

### When Adding New Features

#### 1. Database Changes
- Add migrations in `src/data/migrations/`
- Update both SQLite and PostgreSQL schemas
- Test with both database types

#### 2. New Models
- Extend `BaseEntity` for consistency
- Add to `src/core/models.py`
- Include validation in model

#### 3. New Services
- Create service class in `src/services/`
- Follow existing patterns (caching, error handling)
- Add to `service_layer.py` imports

#### 4. UI Components
- Add new pages to `src/ui/pages/`
- Update navigation in `main.py`
- Follow Streamlit best practices

#### 5. Security Considerations
- Use `@login_required` for protected routes
- Validate all inputs
- Add rate limiting where appropriate

### Recommended Extension Points

#### 1. API Layer
```python
# Add REST API for mobile apps
# src/api/
├── __init__.py
├── routes/
│   ├── auth.py
│   ├── clients.py
│   └── assessments.py
└── middleware/
    ├── auth.py
    └── rate_limit.py
```

#### 2. Notification System
```python
# Add email/SMS notifications
# src/notifications/
├── __init__.py
├── email_service.py
├── sms_service.py
└── templates/
```

#### 3. Advanced Analytics
```python
# Machine learning insights
# src/ml/
├── __init__.py
├── prediction_models.py
├── anomaly_detection.py
└── recommendation_engine.py
```

#### 4. Integration Layer
```python
# Third-party integrations
# src/integrations/
├── __init__.py
├── payment_gateways/
├── calendar_sync/
└── wearable_devices/
```

### Performance Optimization Tips

1. **Database Queries**
   - Add indexes for frequently queried fields
   - Use query optimization techniques
   - Consider read replicas for scaling

2. **Caching**
   - Add Redis for distributed caching
   - Implement cache warming strategies
   - Use cache-aside pattern

3. **Async Operations**
   - Use Celery for background tasks
   - Implement message queues
   - Add webhook support

### Testing Guidelines

1. **Unit Tests**
   - Test services independently
   - Mock repository layer
   - Cover edge cases

2. **Integration Tests**
   - Test database operations
   - Verify service interactions
   - Test with both databases

3. **UI Tests**
   - Use Selenium for E2E tests
   - Test critical user flows
   - Verify responsive design

### Deployment Checklist

1. **Environment Variables**
   - DATABASE_URL
   - SECRET_KEY
   - REDIS_URL (if added)
   - EMAIL_API_KEY (if added)

2. **Database Migrations**
   - Run migration scripts
   - Backup existing data
   - Verify schema changes

3. **Security Audit**
   - Update dependencies
   - Check for vulnerabilities
   - Review access controls

4. **Performance Testing**
   - Load test with realistic data
   - Monitor response times
   - Check memory usage

## Conclusion

This architecture document provides a comprehensive overview of The5HC Fitness Assessment System. The modular design, clear separation of concerns, and extensive use of design patterns make it easy to extend and maintain. When planning new features, follow the established patterns and consider the security, performance, and scalability implications outlined in this guide.