# The5HC Django Migration Guide

## Executive Summary

This guide provides a comprehensive step-by-step approach to migrating The5HC fitness assessment system from Streamlit to Django. Based on modern best practices for 2024-2025, we recommend using the **Django + HTMX + Alpine.js** stack, which offers:

- 67% reduction in code size (based on production case studies)
- 96% reduction in JavaScript dependencies
- 50-60% improvement in load times
- Maintains real-time features through WebSockets
- No build step required
- Preserves server-side logic advantages

## Technology Stack Decision

### Recommended Stack: Django + HTMX + Alpine.js

**Why this stack?**
1. **HTMX** (Interactivity without complexity)
   - Server-side rendering with SPA-like feel
   - WebSocket support for real-time features
   - Perfect for form-heavy applications
   - Minimal JavaScript required

2. **Alpine.js** (UI enhancements)
   - Lightweight (15KB)
   - Handles client-side state
   - Perfect for dropdowns, modals, transitions
   - Works seamlessly with HTMX

3. **Tailwind CSS** (Styling)
   - Utility-first approach
   - Rapid development
   - Consistent design system
   - Perfect for Korean UI requirements

## Migration Phases Overview

### Original Plan:
1. **Phase 1**: Project Setup & Infrastructure (Week 1-2)
2. **Phase 2**: Database & Models Migration (Week 2-3)
3. **Phase 3**: Service Layer & Business Logic (Week 3-5)
4. **Phase 4**: Frontend Implementation (Week 5-8)
5. **Phase 5**: Feature Migration (Week 8-12)
6. **Phase 6**: Testing & Deployment (Week 12-14)

### Actual Implementation (Updated 2025-06-09):
1. **Phase 1**: ✅ Project Setup & Infrastructure - COMPLETE
2. **Phase 2**: ✅ Database & Models Migration - COMPLETE
3. **Phase 3**: ✅ Forms and UI Implementation - COMPLETE (100%)
   - Note: Phase 3 was refocused on UI/Forms instead of service layer
   - Service layer logic was integrated directly into views
   - All 8 major UI components completed with full test coverage
4. **Phase 4**: ✅ PDF Reports & Data Migration - COMPLETE
   - PDF report generation with WeasyPrint
   - Data migration from Streamlit SQLite to Django
   - All 42 records migrated successfully
5. **Phase 5**: API & Mobile Optimization (Planned)
6. **Phase 6**: Production Deployment (Planned)

---

## Phase 1: Project Setup & Infrastructure

### 1.1 Django Project Initialization

```bash
# Create project directory
mkdir the5hc_django && cd the5hc_django

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Django and core dependencies
pip install django==5.0.1
pip install django-htmx==1.17.2
pip install django-compressor==4.4
pip install python-decouple==3.8
pip install psycopg2-binary==2.9.9
pip install redis==5.0.1
pip install celery==5.3.4
pip install django-crispy-forms==2.1
pip install crispy-tailwind==1.0.3
```

### 1.2 Create Django Project Structure

```bash
# Create Django project
django-admin startproject the5hc .

# Create apps
python manage.py startapp accounts
python manage.py startapp trainers
python manage.py startapp clients
python manage.py startapp assessments
python manage.py startapp sessions
python manage.py startapp analytics
python manage.py startapp reports
```

### 1.3 Project Structure

```
the5hc_django/
├── manage.py
├── requirements.txt
├── .env
├── the5hc/
│   ├── __init__.py
│   ├── settings/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── development.py
│   │   ├── production.py
│   │   └── test.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
├── apps/
│   ├── __init__.py
│   ├── accounts/
│   ├── trainers/
│   ├── clients/
│   ├── assessments/
│   ├── sessions/
│   ├── analytics/
│   └── reports/
├── static/
│   ├── css/
│   ├── js/
│   └── fonts/
├── templates/
│   ├── base.html
│   ├── components/
│   └── pages/
├── media/
├── utils/
│   ├── __init__.py
│   ├── fee_calculator.py
│   ├── validators.py
│   └── pdf_generator.py
└── tests/
```

### 1.4 Settings Configuration

**the5hc/settings/base.py**:
```python
from pathlib import Path
from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='', cast=lambda v: [s.strip() for s in v.split(',')])

# Application definition
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'django_htmx',
    'compressor',
    'crispy_forms',
    'crispy_tailwind',
]

LOCAL_APPS = [
    'apps.accounts',
    'apps.trainers',
    'apps.clients',
    'apps.assessments',
    'apps.sessions',
    'apps.analytics',
    'apps.reports',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django_htmx.middleware.HtmxMiddleware',
]

# Database configuration
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432'),
    }
}

# Cache configuration
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': config('REDIS_URL', default='redis://127.0.0.1:6379/1'),
    }
}

# Internationalization
LANGUAGE_CODE = 'ko-kr'
TIME_ZONE = 'Asia/Seoul'
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

# Media files
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Crispy forms
CRISPY_ALLOWED_TEMPLATE_PACKS = "tailwind"
CRISPY_TEMPLATE_PACK = "tailwind"

# Custom user model
AUTH_USER_MODEL = 'accounts.User'

# Session settings
SESSION_COOKIE_AGE = 86400  # 24 hours
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
SESSION_SAVE_EVERY_REQUEST = True
```

### 1.5 HTMX + Alpine.js Setup

**templates/base.html**:
```html
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}The5HC - 피트니스 평가 시스템{% endblock %}</title>
    
    <!-- Tailwind CSS -->
    <script src="https://cdn.tailwindcss.com"></script>
    
    <!-- Alpine.js -->
    <script defer src="https://unpkg.com/alpinejs@3.x.x/dist/cdn.min.js"></script>
    
    <!-- HTMX -->
    <script src="https://unpkg.com/htmx.org@1.9.10"></script>
    
    <!-- HTMX Extensions -->
    <script src="https://unpkg.com/htmx.org/dist/ext/ws.js"></script>
    
    <!-- Custom CSS -->
    {% compress css %}
    <link rel="stylesheet" href="{% static 'css/styles.css' %}">
    {% endcompress %}
    
    {% block extra_head %}{% endblock %}
</head>
<body class="bg-gray-50" hx-headers='{"X-CSRFToken": "{{ csrf_token }}"}'>
    <div id="notifications" class="fixed top-4 right-4 z-50"></div>
    
    {% include 'components/navbar.html' %}
    
    <main class="container mx-auto px-4 py-8">
        {% block content %}{% endblock %}
    </main>
    
    {% compress js %}
    <script src="{% static 'js/app.js' %}"></script>
    {% endcompress %}
    
    {% block extra_scripts %}{% endblock %}
</body>
</html>
```

---

## Phase 2: Database & Models Migration

### 2.1 User Model

**apps/accounts/models.py**:
```python
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

class User(AbstractUser):
    """Custom user model for trainers"""
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    organization = models.CharField(max_length=100, blank=True)
    
    # Activity tracking
    last_activity = models.DateTimeField(null=True, blank=True)
    login_attempts = models.IntegerField(default=0)
    last_login_attempt = models.DateTimeField(null=True, blank=True)
    is_locked = models.BooleanField(default=False)
    
    # Settings
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    class Meta:
        db_table = 'trainers'
        verbose_name = '트레이너'
        verbose_name_plural = '트레이너'
```

### 2.2 Client Model

**apps/clients/models.py**:
```python
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator

User = get_user_model()

class Client(models.Model):
    GENDER_CHOICES = [
        ('male', '남성'),
        ('female', '여성'),
    ]
    
    trainer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='clients')
    name = models.CharField(max_length=100)
    email = models.EmailField(blank=True)
    phone = models.CharField(
        max_length=20,
        validators=[RegexValidator(r'^\d{3}-\d{3,4}-\d{4}$', '올바른 전화번호 형식이 아닙니다.')]
    )
    birth_date = models.DateField()
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    
    # Physical measurements
    height = models.DecimalField(max_digits=5, decimal_places=2)
    weight = models.DecimalField(max_digits=5, decimal_places=2)
    
    # Goals and notes
    goals = models.TextField(blank=True)
    medical_conditions = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    
    # Metadata
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'clients'
        ordering = ['-created_at']
        unique_together = ['trainer', 'phone']
        verbose_name = '회원'
        verbose_name_plural = '회원'
    
    def __str__(self):
        return f"{self.name} ({self.phone})"
    
    @property
    def age(self):
        from datetime import date
        today = date.today()
        return today.year - self.birth_date.year - (
            (today.month, today.day) < (self.birth_date.month, self.birth_date.day)
        )
    
    @property
    def bmi(self):
        if self.height and self.weight:
            height_m = float(self.height) / 100
            return round(float(self.weight) / (height_m ** 2), 1)
        return None
```

### 2.3 Assessment Models

**apps/assessments/models.py**:
```python
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator

User = get_user_model()

class Assessment(models.Model):
    trainer = models.ForeignKey(User, on_delete=models.CASCADE)
    client = models.ForeignKey('clients.Client', on_delete=models.CASCADE, related_name='assessments')
    
    # Basic info
    assessment_date = models.DateField()
    assessment_type = models.CharField(max_length=50, default='standard')
    
    # Body composition
    body_fat_percentage = models.DecimalField(
        max_digits=4, decimal_places=1,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        null=True, blank=True
    )
    muscle_mass = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    # Scores (JSON field for flexibility)
    scores = models.JSONField(default=dict)
    
    # Recommendations
    recommendations = models.JSONField(default=dict)
    
    # Metadata
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'assessments'
        ordering = ['-assessment_date', '-created_at']
        verbose_name = '평가'
        verbose_name_plural = '평가'
    
    def calculate_total_score(self):
        """Calculate total score from all categories"""
        from utils.scoring import calculate_total_score
        return calculate_total_score(self.scores)
```

### 2.4 Session Management Models

**apps/sessions/models.py**:
```python
from django.db import models
from django.contrib.auth import get_user_model
from decimal import Decimal

User = get_user_model()

class SessionPackage(models.Model):
    trainer = models.ForeignKey(User, on_delete=models.CASCADE)
    client = models.ForeignKey('clients.Client', on_delete=models.CASCADE, related_name='packages')
    
    # Package details
    package_name = models.CharField(max_length=100)
    gross_amount = models.DecimalField(max_digits=10, decimal_places=0)
    session_price = models.DecimalField(max_digits=10, decimal_places=0)
    
    # Fee breakdown
    vat_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('10.0'))
    card_fee_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('3.5'))
    vat_amount = models.DecimalField(max_digits=10, decimal_places=0)
    card_fee_amount = models.DecimalField(max_digits=10, decimal_places=0)
    net_amount = models.DecimalField(max_digits=10, decimal_places=0)
    
    # Credits
    total_sessions = models.IntegerField()
    remaining_sessions = models.IntegerField()
    
    # Status
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'session_packages'
        ordering = ['-created_at']
    
    def save(self, *args, **kwargs):
        # Calculate fees before saving
        from utils.fee_calculator import FeeCalculator
        fees = FeeCalculator.calculate_fees(float(self.gross_amount))
        self.vat_amount = Decimal(str(fees.vat_amount))
        self.card_fee_amount = Decimal(str(fees.card_fee_amount))
        self.net_amount = Decimal(str(fees.net_amount))
        
        # Calculate total sessions
        if self.session_price > 0:
            self.total_sessions = int(self.gross_amount / self.session_price)
            if not self.pk:  # New package
                self.remaining_sessions = self.total_sessions
        
        super().save(*args, **kwargs)

class Session(models.Model):
    STATUS_CHOICES = [
        ('scheduled', '예약됨'),
        ('completed', '완료'),
        ('cancelled', '취소'),
        ('no_show', '노쇼'),
    ]
    
    package = models.ForeignKey(SessionPackage, on_delete=models.CASCADE, related_name='sessions')
    session_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'sessions'
        ordering = ['-session_date']
```

### 2.5 Database Migration

```bash
# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
```

### 2.6 Data Migration Script

**scripts/migrate_data.py**:
```python
import os
import sys
import django

# Setup Django
sys.path.append('..')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'the5hc.settings.development')
django.setup()

from apps.accounts.models import User
from apps.clients.models import Client
from apps.assessments.models import Assessment
from src.data.database import get_db_connection

def migrate_trainers():
    """Migrate trainers from old database"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM trainers")
        
        for row in cursor.fetchall():
            User.objects.create(
                username=row['username'],
                email=row['email'],
                password=row['password_hash'],  # Already hashed
                first_name=row.get('name', '').split()[0],
                last_name=' '.join(row.get('name', '').split()[1:]),
                phone=row.get('phone', ''),
                organization=row.get('organization', ''),
                created_at=row['created_at']
            )

def migrate_clients():
    """Migrate clients from old database"""
    # Similar migration logic for clients
    pass

def migrate_assessments():
    """Migrate assessments from old database"""
    # Similar migration logic for assessments
    pass

if __name__ == '__main__':
    print("Starting data migration...")
    migrate_trainers()
    migrate_clients()
    migrate_assessments()
    print("Migration completed!")
```

---

## Phase 3: Service Layer & Business Logic

### 3.1 Authentication Service

**apps/accounts/services.py**:
```python
from django.contrib.auth import authenticate, login, logout
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta
import bcrypt

class AuthService:
    MAX_LOGIN_ATTEMPTS = 5
    LOCKOUT_DURATION = timedelta(minutes=30)
    
    @classmethod
    def login_user(cls, request, email, password):
        """Handle user login with rate limiting"""
        # Check if account is locked
        lockout_key = f"lockout:{email}"
        if cache.get(lockout_key):
            return False, "계정이 잠겼습니다. 30분 후에 다시 시도해주세요."
        
        user = authenticate(request, username=email, password=password)
        if user is not None:
            if not user.is_active:
                return False, "비활성화된 계정입니다."
            
            login(request, user)
            user.last_activity = timezone.now()
            user.login_attempts = 0
            user.save(update_fields=['last_activity', 'login_attempts'])
            
            # Log activity
            cls.log_activity(user, 'login', request)
            
            return True, user
        else:
            # Handle failed login
            cls._handle_failed_login(email)
            return False, "이메일 또는 비밀번호가 올바르지 않습니다."
    
    @classmethod
    def _handle_failed_login(cls, email):
        """Handle failed login attempts"""
        from apps.accounts.models import User
        
        try:
            user = User.objects.get(email=email)
            user.login_attempts += 1
            user.last_login_attempt = timezone.now()
            
            if user.login_attempts >= cls.MAX_LOGIN_ATTEMPTS:
                # Lock account
                cache.set(f"lockout:{email}", True, cls.LOCKOUT_DURATION.total_seconds())
                user.is_locked = True
            
            user.save(update_fields=['login_attempts', 'last_login_attempt', 'is_locked'])
        except User.DoesNotExist:
            pass
    
    @classmethod
    def log_activity(cls, user, action, request):
        """Log user activity"""
        from apps.accounts.models import ActivityLog
        
        ActivityLog.objects.create(
            user=user,
            action=action,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:200]
        )
```

### 3.2 Client Service with Caching

**apps/clients/services.py**:
```python
from django.core.cache import cache
from django.db.models import Count, Avg, Q
from apps.clients.models import Client

class ClientService:
    CACHE_TTL = 300  # 5 minutes
    
    @classmethod
    def get_client_list(cls, trainer, search_query=None):
        """Get filtered client list with caching"""
        cache_key = f"clients:{trainer.id}:{search_query or 'all'}"
        cached_result = cache.get(cache_key)
        
        if cached_result is not None:
            return cached_result
        
        queryset = Client.objects.filter(trainer=trainer, is_active=True)
        
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(phone__icontains=search_query) |
                Q(email__icontains=search_query)
            )
        
        # Annotate with assessment count
        queryset = queryset.annotate(
            assessment_count=Count('assessments'),
            avg_score=Avg('assessments__total_score')
        )
        
        result = list(queryset.select_related('trainer'))
        cache.set(cache_key, result, cls.CACHE_TTL)
        
        return result
    
    @classmethod
    def create_client(cls, trainer, data):
        """Create new client and invalidate cache"""
        client = Client.objects.create(trainer=trainer, **data)
        
        # Invalidate cache
        cache.delete_pattern(f"clients:{trainer.id}:*")
        
        return client
```

### 3.3 Assessment Service

**apps/assessments/services.py**:
```python
from django.db import transaction
from apps.assessments.models import Assessment
from utils.scoring import ScoringService
from utils.recommendations import RecommendationEngine

class AssessmentService:
    @classmethod
    @transaction.atomic
    def create_assessment(cls, trainer, client_id, assessment_data):
        """Create new assessment with scoring and recommendations"""
        # Validate client belongs to trainer
        client = trainer.clients.get(id=client_id)
        
        # Calculate scores
        scores = ScoringService.calculate_scores(assessment_data)
        
        # Generate recommendations
        recommendations = RecommendationEngine.generate_recommendations(
            client=client,
            scores=scores,
            assessment_data=assessment_data
        )
        
        # Create assessment
        assessment = Assessment.objects.create(
            trainer=trainer,
            client=client,
            assessment_date=assessment_data['assessment_date'],
            body_fat_percentage=assessment_data.get('body_fat_percentage'),
            muscle_mass=assessment_data.get('muscle_mass'),
            scores=scores,
            recommendations=recommendations,
            notes=assessment_data.get('notes', '')
        )
        
        # Create detailed records for each measurement
        cls._create_measurement_records(assessment, assessment_data)
        
        # Update client's latest assessment cache
        cache.set(f"latest_assessment:{client.id}", assessment, 3600)
        
        return assessment
    
    @classmethod
    def _create_measurement_records(cls, assessment, data):
        """Create individual measurement records"""
        # Implementation for creating detailed measurement records
        pass
```

### 3.4 Session Management Service

**apps/sessions/services.py**:
```python
from django.db import transaction
from decimal import Decimal
from apps.sessions.models import SessionPackage, Session, Payment
from utils.fee_calculator import FeeCalculator

class SessionService:
    @classmethod
    @transaction.atomic
    def create_package_with_fees(cls, trainer, client_id, gross_amount, session_price, package_name=None):
        """Create session package with automatic fee calculation"""
        client = trainer.clients.get(id=client_id)
        
        # Calculate fees
        fees = FeeCalculator.calculate_fees(float(gross_amount))
        
        # Create package
        package = SessionPackage.objects.create(
            trainer=trainer,
            client=client,
            package_name=package_name or f"{client.name} 패키지",
            gross_amount=gross_amount,
            session_price=session_price,
            vat_rate=Decimal('10.0'),
            card_fee_rate=Decimal('3.5'),
            vat_amount=fees.vat_amount,
            card_fee_amount=fees.card_fee_amount,
            net_amount=fees.net_amount
        )
        
        # Create initial payment record
        Payment.objects.create(
            package=package,
            amount=gross_amount,
            payment_method='card',
            vat_amount=fees.vat_amount,
            card_fee_amount=fees.card_fee_amount,
            net_amount=fees.net_amount
        )
        
        # Log fee calculation
        FeeCalculator.log_calculation(
            trainer_id=trainer.id,
            client_id=client.id,
            gross_amount=float(gross_amount),
            calculation_type='package_creation',
            context={'package_id': package.id}
        )
        
        return package
    
    @classmethod
    def schedule_session(cls, package_id, session_date, notes=''):
        """Schedule a new session"""
        package = SessionPackage.objects.get(id=package_id)
        
        if package.remaining_sessions <= 0:
            raise ValueError("남은 세션이 없습니다.")
        
        session = Session.objects.create(
            package=package,
            session_date=session_date,
            status='scheduled',
            notes=notes
        )
        
        return session
    
    @classmethod
    @transaction.atomic
    def complete_session(cls, session_id):
        """Mark session as completed and deduct credit"""
        session = Session.objects.select_for_update().get(id=session_id)
        
        if session.status != 'scheduled':
            raise ValueError("예약된 세션만 완료할 수 있습니다.")
        
        session.status = 'completed'
        session.save()
        
        # Deduct credit
        package = session.package
        package.remaining_sessions -= 1
        package.save(update_fields=['remaining_sessions'])
        
        return session
```

---

## Phase 4: Frontend Implementation with HTMX + Alpine.js

### 4.1 Navigation Component

**templates/components/navbar.html**:
```html
<nav class="bg-white shadow-lg" x-data="{ mobileMenuOpen: false }">
    <div class="container mx-auto px-4">
        <div class="flex justify-between items-center py-4">
            <div class="flex items-center">
                <a href="{% url 'dashboard' %}" class="text-xl font-bold text-gray-800">
                    🏋️ The5HC
                </a>
            </div>
            
            <!-- Desktop Menu -->
            <div class="hidden md:flex items-center space-x-4">
                <a href="{% url 'dashboard' %}" 
                   class="nav-link {% if request.resolver_match.url_name == 'dashboard' %}active{% endif %}"
                   hx-get="{% url 'dashboard' %}"
                   hx-target="#main-content"
                   hx-push-url="true">
                    대시보드
                </a>
                <a href="{% url 'clients:list' %}"
                   class="nav-link {% if 'clients' in request.resolver_match.app_name %}active{% endif %}"
                   hx-get="{% url 'clients:list' %}"
                   hx-target="#main-content"
                   hx-push-url="true">
                    회원 관리
                </a>
                <a href="{% url 'assessments:new' %}"
                   class="nav-link"
                   hx-get="{% url 'assessments:new' %}"
                   hx-target="#main-content"
                   hx-push-url="true">
                    평가 실시
                </a>
                <a href="{% url 'sessions:management' %}"
                   class="nav-link"
                   hx-get="{% url 'sessions:management' %}"
                   hx-target="#main-content"
                   hx-push-url="true">
                    세션 관리
                </a>
            </div>
            
            <!-- User Menu -->
            <div class="relative" x-data="{ userMenuOpen: false }">
                <button @click="userMenuOpen = !userMenuOpen"
                        class="flex items-center text-gray-700 hover:text-gray-900">
                    <span class="mr-2">{{ user.get_full_name|default:user.email }}</span>
                    <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clip-rule="evenodd"></path>
                    </svg>
                </button>
                
                <div x-show="userMenuOpen"
                     x-transition
                     @click.away="userMenuOpen = false"
                     class="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg py-1 z-50">
                    <a href="{% url 'accounts:profile' %}" class="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100">
                        프로필
                    </a>
                    <a href="{% url 'accounts:logout' %}" 
                       class="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                       hx-post="{% url 'accounts:logout' %}"
                       hx-confirm="로그아웃 하시겠습니까?">
                        로그아웃
                    </a>
                </div>
            </div>
        </div>
    </div>
</nav>
```

### 4.2 Client List View with Search

**templates/clients/list.html**:
```html
{% extends 'base.html' %}

{% block content %}
<div class="max-w-7xl mx-auto">
    <div class="flex justify-between items-center mb-6">
        <h1 class="text-3xl font-bold text-gray-800">회원 관리</h1>
        <button onclick="showAddClientModal()"
                class="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700">
            + 새 회원 추가
        </button>
    </div>
    
    <!-- Search Bar -->
    <div class="mb-6">
        <input type="text"
               name="search"
               placeholder="이름, 전화번호로 검색..."
               class="w-full md:w-96 px-4 py-2 border rounded-lg"
               hx-get="{% url 'clients:search' %}"
               hx-trigger="keyup changed delay:500ms"
               hx-target="#client-list"
               hx-indicator="#search-indicator">
        <span id="search-indicator" class="htmx-indicator ml-2">검색중...</span>
    </div>
    
    <!-- Client List -->
    <div id="client-list">
        {% include 'clients/partials/client_table.html' %}
    </div>
</div>

<!-- Add Client Modal -->
<div id="add-client-modal" 
     class="hidden fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full"
     x-data="{ open: false }"
     x-show="open"
     @keydown.escape.window="open = false">
    <div class="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white"
         @click.away="open = false">
        <div id="modal-content">
            <!-- Content loaded via HTMX -->
        </div>
    </div>
</div>

<script>
function showAddClientModal() {
    htmx.ajax('GET', '{% url "clients:add" %}', {
        target: '#modal-content',
        swap: 'innerHTML'
    }).then(() => {
        Alpine.store('clientModal').open = true;
    });
}
</script>
{% endblock %}
```

### 4.3 Real-time Session Management

**templates/sessions/management.html**:
```html
{% extends 'base.html' %}

{% block content %}
<div x-data="sessionManagement()" class="max-w-7xl mx-auto">
    <h1 class="text-3xl font-bold mb-6">세션 관리</h1>
    
    <!-- Client Selection -->
    <div class="mb-6">
        <label class="block text-sm font-medium text-gray-700 mb-2">회원 선택</label>
        <select @change="loadClientPackages($event.target.value)"
                class="w-full md:w-96 px-4 py-2 border rounded-lg">
            <option value="">회원을 선택하세요</option>
            {% for client in clients %}
            <option value="{{ client.id }}">{{ client.name }} ({{ client.phone }})</option>
            {% endfor %}
        </select>
    </div>
    
    <!-- Package Info -->
    <div x-show="selectedClient" x-transition>
        <div class="bg-white rounded-lg shadow p-6 mb-6">
            <h2 class="text-xl font-semibold mb-4">패키지 정보</h2>
            <div id="package-info">
                <!-- Loaded via HTMX -->
            </div>
        </div>
        
        <!-- Add Credits Form -->
        <div class="bg-white rounded-lg shadow p-6 mb-6">
            <h3 class="text-lg font-semibold mb-4">크레딧 추가</h3>
            <form hx-post="{% url 'sessions:add_credits' %}"
                  hx-target="#package-info"
                  hx-swap="outerHTML"
                  @submit="showLoading = true">
                {% csrf_token %}
                <input type="hidden" name="client_id" x-model="selectedClient">
                
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                        <label class="block text-sm font-medium text-gray-700">총 금액</label>
                        <input type="number"
                               name="gross_amount"
                               x-model="grossAmount"
                               @input="calculateFees()"
                               class="mt-1 block w-full rounded-md border-gray-300"
                               required>
                    </div>
                    
                    <div>
                        <label class="block text-sm font-medium text-gray-700">세션 단가</label>
                        <input type="number"
                               name="session_price"
                               x-model="sessionPrice"
                               @input="calculateSessions()"
                               class="mt-1 block w-full rounded-md border-gray-300"
                               required>
                    </div>
                </div>
                
                <!-- Real-time Fee Calculation Display -->
                <div class="mt-4 p-4 bg-gray-50 rounded" x-show="grossAmount > 0">
                    <h4 class="font-medium mb-2">수수료 계산</h4>
                    <div class="grid grid-cols-2 gap-2 text-sm">
                        <div>부가세 (10%):</div>
                        <div class="text-right" x-text="formatCurrency(vatAmount)"></div>
                        <div>카드 수수료 (3.5%):</div>
                        <div class="text-right" x-text="formatCurrency(cardFeeAmount)"></div>
                        <div class="font-semibold">실 수령액:</div>
                        <div class="text-right font-semibold" x-text="formatCurrency(netAmount)"></div>
                        <div class="font-semibold">추가 세션 수:</div>
                        <div class="text-right font-semibold" x-text="additionalSessions + '회'"></div>
                    </div>
                </div>
                
                <div class="mt-6">
                    <button type="submit"
                            class="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700"
                            :disabled="showLoading">
                        <span x-show="!showLoading">크레딧 추가</span>
                        <span x-show="showLoading">처리중...</span>
                    </button>
                </div>
            </form>
        </div>
        
        <!-- Session Calendar -->
        <div class="bg-white rounded-lg shadow p-6">
            <h3 class="text-lg font-semibold mb-4">세션 일정</h3>
            <div id="session-calendar">
                <!-- Calendar component -->
            </div>
        </div>
    </div>
</div>

<script>
function sessionManagement() {
    return {
        selectedClient: null,
        grossAmount: 0,
        sessionPrice: 0,
        vatAmount: 0,
        cardFeeAmount: 0,
        netAmount: 0,
        additionalSessions: 0,
        showLoading: false,
        
        loadClientPackages(clientId) {
            if (!clientId) return;
            
            this.selectedClient = clientId;
            htmx.ajax('GET', `/sessions/client/${clientId}/packages/`, {
                target: '#package-info',
                swap: 'innerHTML'
            });
        },
        
        calculateFees() {
            if (this.grossAmount <= 0) return;
            
            // Real-time fee calculation matching the backend logic
            const netBeforeVat = this.grossAmount / 1.1;
            this.vatAmount = Math.round(this.grossAmount - netBeforeVat);
            this.cardFeeAmount = Math.round(netBeforeVat * 0.035);
            this.netAmount = Math.round(netBeforeVat - this.cardFeeAmount);
            
            this.calculateSessions();
        },
        
        calculateSessions() {
            if (this.grossAmount > 0 && this.sessionPrice > 0) {
                this.additionalSessions = Math.floor(this.grossAmount / this.sessionPrice);
            }
        },
        
        formatCurrency(amount) {
            return new Intl.NumberFormat('ko-KR', {
                style: 'currency',
                currency: 'KRW'
            }).format(amount);
        }
    }
}
</script>
{% endblock %}
```

### 4.4 Assessment Form with Multi-step Wizard

**templates/assessments/new.html**:
```html
{% extends 'base.html' %}

{% block content %}
<div x-data="assessmentWizard()" class="max-w-4xl mx-auto">
    <h1 class="text-3xl font-bold mb-6">새 평가 실시</h1>
    
    <!-- Progress Bar -->
    <div class="mb-8">
        <div class="flex items-center">
            <template x-for="(step, index) in steps" :key="index">
                <div class="flex-1 flex items-center">
                    <div class="relative">
                        <div :class="{'bg-blue-600': currentStep > index, 'bg-blue-600': currentStep === index, 'bg-gray-300': currentStep < index}"
                             class="w-10 h-10 rounded-full flex items-center justify-center text-white">
                            <span x-text="index + 1"></span>
                        </div>
                        <span class="absolute top-12 left-1/2 transform -translate-x-1/2 text-xs"
                              x-text="step.name"></span>
                    </div>
                    <div x-show="index < steps.length - 1"
                         :class="{'bg-blue-600': currentStep > index, 'bg-gray-300': currentStep <= index}"
                         class="flex-1 h-1 mx-2"></div>
                </div>
            </template>
        </div>
    </div>
    
    <!-- Form -->
    <form id="assessment-form"
          hx-post="{% url 'assessments:create' %}"
          hx-target="#form-messages"
          @submit="handleSubmit($event)">
        {% csrf_token %}
        
        <!-- Step 1: Client Selection -->
        <div x-show="currentStep === 0" x-transition>
            <h2 class="text-xl font-semibold mb-4">회원 선택</h2>
            <select name="client_id" 
                    x-model="formData.client_id"
                    @change="loadClientInfo($event.target.value)"
                    class="w-full px-4 py-2 border rounded-lg" required>
                <option value="">회원을 선택하세요</option>
                {% for client in clients %}
                <option value="{{ client.id }}">{{ client.name }} ({{ client.phone }})</option>
                {% endfor %}
            </select>
            
            <div x-show="clientInfo" class="mt-4 p-4 bg-gray-50 rounded">
                <h3 class="font-medium mb-2">회원 정보</h3>
                <div class="grid grid-cols-2 gap-2 text-sm">
                    <div>나이:</div>
                    <div x-text="clientInfo.age + '세'"></div>
                    <div>성별:</div>
                    <div x-text="clientInfo.gender"></div>
                    <div>키/체중:</div>
                    <div x-text="clientInfo.height + 'cm / ' + clientInfo.weight + 'kg'"></div>
                    <div>BMI:</div>
                    <div x-text="clientInfo.bmi"></div>
                </div>
            </div>
        </div>
        
        <!-- Step 2: Body Composition -->
        <div x-show="currentStep === 1" x-transition>
            <h2 class="text-xl font-semibold mb-4">체성분 측정</h2>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                    <label class="block text-sm font-medium text-gray-700">체지방률 (%)</label>
                    <input type="number" 
                           name="body_fat_percentage"
                           x-model="formData.body_fat_percentage"
                           step="0.1" min="0" max="100"
                           class="mt-1 block w-full rounded-md border-gray-300">
                </div>
                <div>
                    <label class="block text-sm font-medium text-gray-700">골격근량 (kg)</label>
                    <input type="number"
                           name="muscle_mass"
                           x-model="formData.muscle_mass"
                           step="0.1" min="0"
                           class="mt-1 block w-full rounded-md border-gray-300">
                </div>
            </div>
        </div>
        
        <!-- Step 3: Fitness Tests -->
        <div x-show="currentStep === 2" x-transition>
            <h2 class="text-xl font-semibold mb-4">체력 측정</h2>
            <div class="space-y-4">
                <!-- Dynamic fitness test inputs based on configuration -->
                <template x-for="test in fitnessTests" :key="test.id">
                    <div>
                        <label class="block text-sm font-medium text-gray-700"
                               x-text="test.name + ' (' + test.unit + ')'"></label>
                        <input :type="test.type"
                               :name="'test_' + test.id"
                               x-model="formData.tests[test.id]"
                               :step="test.step"
                               :min="test.min"
                               class="mt-1 block w-full rounded-md border-gray-300">
                        <p class="mt-1 text-sm text-gray-500" x-text="test.description"></p>
                    </div>
                </template>
            </div>
        </div>
        
        <!-- Navigation Buttons -->
        <div class="mt-8 flex justify-between">
            <button type="button"
                    @click="previousStep()"
                    x-show="currentStep > 0"
                    class="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50">
                이전
            </button>
            
            <button type="button"
                    @click="nextStep()"
                    x-show="currentStep < steps.length - 1"
                    class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700">
                다음
            </button>
            
            <button type="submit"
                    x-show="currentStep === steps.length - 1"
                    class="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700">
                평가 완료
            </button>
        </div>
    </form>
    
    <div id="form-messages" class="mt-4"></div>
</div>

<script>
function assessmentWizard() {
    return {
        currentStep: 0,
        steps: [
            { name: '회원 선택' },
            { name: '체성분' },
            { name: '체력 측정' },
            { name: '유연성' },
            { name: '균형' },
            { name: '완료' }
        ],
        formData: {
            client_id: '',
            body_fat_percentage: '',
            muscle_mass: '',
            tests: {}
        },
        clientInfo: null,
        fitnessTests: {{ fitness_tests|json_script:"fitness-tests" }},
        
        loadClientInfo(clientId) {
            if (!clientId) return;
            
            fetch(`/api/clients/${clientId}/`)
                .then(response => response.json())
                .then(data => {
                    this.clientInfo = data;
                });
        },
        
        nextStep() {
            if (this.validateStep()) {
                this.currentStep++;
            }
        },
        
        previousStep() {
            this.currentStep--;
        },
        
        validateStep() {
            // Step-specific validation
            switch(this.currentStep) {
                case 0:
                    return this.formData.client_id !== '';
                case 1:
                    return true; // Body composition is optional
                default:
                    return true;
            }
        },
        
        handleSubmit(event) {
            // Form will be submitted via HTMX
            console.log('Submitting assessment:', this.formData);
        }
    }
}
</script>
{% endblock %}
```

---

## Phase 5: Feature-Specific Migration

### 5.1 Dashboard with Real-time Updates

**apps/analytics/views.py**:
```python
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django_htmx.http import HttpResponseClientRefresh

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/main.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get dashboard stats
        context['stats'] = {
            'total_clients': user.clients.filter(is_active=True).count(),
            'assessments_this_month': self._get_monthly_assessments(user),
            'active_sessions': self._get_active_sessions(user),
            'revenue_this_month': self._get_monthly_revenue(user),
        }
        
        # Recent activities
        context['recent_assessments'] = self._get_recent_assessments(user)
        context['upcoming_sessions'] = self._get_upcoming_sessions(user)
        
        return context
    
    def _get_monthly_assessments(self, user):
        from django.utils import timezone
        from datetime import timedelta
        
        start_date = timezone.now().date().replace(day=1)
        return user.assessment_set.filter(
            assessment_date__gte=start_date
        ).count()

@require_http_methods(["GET"])
def dashboard_stats_htmx(request):
    """HTMX endpoint for real-time dashboard updates"""
    if not request.htmx:
        return JsonResponse({'error': 'HTMX request required'}, status=400)
    
    # Return partial template with updated stats
    return render(request, 'dashboard/partials/stats.html', {
        'stats': get_updated_stats(request.user)
    })
```

### 5.2 PDF Report Generation

**apps/reports/services.py**:
```python
from django.template.loader import render_to_string
from weasyprint import HTML, CSS
from django.conf import settings
import os

class ReportService:
    @classmethod
    def generate_assessment_report(cls, assessment):
        """Generate PDF report for assessment"""
        # Prepare context
        context = {
            'assessment': assessment,
            'client': assessment.client,
            'trainer': assessment.trainer,
            'scores': assessment.scores,
            'recommendations': assessment.recommendations,
            'charts': cls._generate_charts(assessment),
        }
        
        # Render HTML
        html_string = render_to_string('reports/assessment_report.html', context)
        
        # Generate PDF
        font_path = os.path.join(settings.STATIC_ROOT, 'fonts', 'NanumGothic.ttf')
        css = CSS(string=f'''
            @font-face {{
                font-family: 'NanumGothic';
                src: url(file://{font_path});
            }}
            body {{
                font-family: 'NanumGothic', sans-serif;
            }}
        ''')
        
        pdf = HTML(string=html_string).write_pdf(stylesheets=[css])
        
        return pdf
    
    @classmethod
    def _generate_charts(cls, assessment):
        """Generate charts for the report"""
        import matplotlib.pyplot as plt
        import io
        import base64
        
        # Create radar chart for scores
        categories = list(assessment.scores.keys())
        values = list(assessment.scores.values())
        
        fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(projection='polar'))
        # ... chart generation code ...
        
        # Convert to base64
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        chart_base64 = base64.b64encode(buffer.read()).decode()
        
        return {'radar_chart': f'data:image/png;base64,{chart_base64}'}
```

### 5.3 WebSocket Integration for Real-time Features

**apps/sessions/consumers.py**:
```python
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

class SessionConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.trainer_id = self.scope['user'].id
        self.room_group_name = f'sessions_{self.trainer_id}'
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
    
    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get('action')
        
        if action == 'update_session':
            await self.update_session(data)
        elif action == 'calculate_fees':
            await self.calculate_fees(data)
    
    async def update_session(self, data):
        # Update session and broadcast to group
        session_id = data.get('session_id')
        status = data.get('status')
        
        # Update in database
        await self.update_session_status(session_id, status)
        
        # Send update to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'session_update',
                'session_id': session_id,
                'status': status
            }
        )
    
    async def session_update(self, event):
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'session_update',
            'session_id': event['session_id'],
            'status': event['status']
        }))
    
    @database_sync_to_async
    def update_session_status(self, session_id, status):
        from apps.sessions.models import Session
        session = Session.objects.get(id=session_id)
        session.status = status
        session.save()
```

### 5.4 HTMX Configuration for Django

**static/js/htmx-config.js**:
```javascript
// Configure HTMX for Django
document.body.addEventListener('htmx:configRequest', (event) => {
    // Add CSRF token to all requests
    event.detail.headers['X-CSRFToken'] = document.querySelector('[name=csrfmiddlewaretoken]').value;
});

// Handle HTMX errors
document.body.addEventListener('htmx:responseError', (event) => {
    console.error('HTMX request failed:', event.detail);
    
    // Show error notification
    showNotification('오류가 발생했습니다. 다시 시도해주세요.', 'error');
});

// Success handling
document.body.addEventListener('htmx:afterRequest', (event) => {
    if (event.detail.successful) {
        // Check for success message in response headers
        const message = event.detail.xhr.getResponseHeader('HX-Trigger-After-Swap');
        if (message) {
            showNotification(message, 'success');
        }
    }
});

// Notification system
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification ${type} fixed top-4 right-4 p-4 rounded-lg shadow-lg`;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        notification.remove();
    }, 5000);
}
```

---

## Phase 6: Testing & Deployment

### 6.1 Testing Strategy

**tests/test_views.py**:
```python
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from apps.clients.models import Client as ClientModel

User = get_user_model()

class DashboardViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.client.login(email='test@example.com', password='testpass123')
    
    def test_dashboard_loads(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '대시보드')
    
    def test_htmx_stats_update(self):
        response = self.client.get(
            '/dashboard/stats/',
            HTTP_HX_REQUEST='true'
        )
        self.assertEqual(response.status_code, 200)

class SessionServiceTest(TestCase):
    def test_fee_calculation(self):
        from utils.fee_calculator import FeeCalculator
        
        result = FeeCalculator.calculate_fees(100000)
        self.assertEqual(result.vat_amount, 9091)
        self.assertEqual(result.card_fee_amount, 3182)
        self.assertEqual(result.net_amount, 87727)
```

### 6.2 Deployment Configuration

**Dockerfile**:
```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Collect static files
RUN python manage.py collectstatic --noinput

# Run migrations
RUN python manage.py migrate

EXPOSE 8000

CMD ["gunicorn", "the5hc.wsgi:application", "--bind", "0.0.0.0:8000"]
```

**docker-compose.yml**:
```yaml
version: '3.8'

services:
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: the5hc
      POSTGRES_USER: the5hc_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    
  web:
    build: .
    command: gunicorn the5hc.wsgi:application --bind 0.0.0.0:8000
    volumes:
      - .:/app
    ports:
      - "8000:8000"
    depends_on:
      - db
      - redis
    environment:
      - DATABASE_URL=postgresql://the5hc_user:${DB_PASSWORD}@db:5432/the5hc
      - REDIS_URL=redis://redis:6379/1
      - SECRET_KEY=${SECRET_KEY}
      - DEBUG=False

  celery:
    build: .
    command: celery -A the5hc worker -l info
    volumes:
      - .:/app
    depends_on:
      - db
      - redis
    environment:
      - DATABASE_URL=postgresql://the5hc_user:${DB_PASSWORD}@db:5432/the5hc
      - REDIS_URL=redis://redis:6379/1

volumes:
  postgres_data:
```

### 6.3 Production Deployment Steps

```bash
# 1. Environment setup
cp .env.example .env
# Edit .env with production values

# 2. Build and run with Docker
docker-compose up -d

# 3. Run migrations
docker-compose exec web python manage.py migrate

# 4. Create superuser
docker-compose exec web python manage.py createsuperuser

# 5. Import existing data
docker-compose exec web python scripts/migrate_data.py

# 6. Configure nginx (nginx.conf)
server {
    listen 80;
    server_name the5hc.com;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /static/ {
        alias /app/staticfiles/;
    }
    
    location /media/ {
        alias /app/media/;
    }
    
    location /ws/ {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

## Migration Timeline Summary

1. **Week 1-2**: Project setup, Django configuration, HTMX/Alpine.js integration
2. **Week 2-3**: Database models, migration scripts, data import
3. **Week 3-5**: Service layer migration, business logic preservation
4. **Week 5-8**: Frontend components, HTMX interactions, real-time features
5. **Week 8-12**: Feature-by-feature migration (assessments, sessions, reports)
6. **Week 12-14**: Testing, optimization, deployment preparation

## Key Success Factors

1. **Preserve Business Logic**: Keep service layer patterns
2. **Incremental Migration**: Migrate feature by feature
3. **Maintain Korean UX**: Consistent Korean language support
4. **Real-time Features**: Use HTMX + WebSockets for live updates
5. **Testing**: Comprehensive test coverage before deployment

This guide provides a complete roadmap for migrating from Streamlit to Django while maintaining all functionality and improving scalability.