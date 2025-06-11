# CI/CD Testing Integration Guide for The5HC

This guide covers setting up automated testing in CI/CD pipelines for The5HC Django project.

## Table of Contents
1. [GitHub Actions Setup](#github-actions-setup)
2. [GitLab CI/CD](#gitlab-cicd)
3. [Pre-commit Hooks](#pre-commit-hooks)
4. [Docker Testing](#docker-testing)
5. [Coverage Requirements](#coverage-requirements)
6. [Environment Setup](#environment-setup)
7. [Best Practices](#best-practices)

## GitHub Actions Setup

### Basic Test Workflow

Create `.github/workflows/tests.yml`:

```yaml
name: Django Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: the5hc_test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Cache pip packages
      uses: actions/cache@v3
      with:
        path: ~/.cache/pip
        key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
        restore-keys: |
          ${{ runner.os }}-pip-
    
    - name: Install system dependencies
      run: |
        sudo apt-get update
        sudo apt-get install -y \
          libpq-dev \
          gettext \
          libcairo2-dev \
          libpango1.0-dev \
          libgdk-pixbuf2.0-dev \
          libffi-dev \
          shared-mime-info
    
    - name: Install Python dependencies
      run: |
        python -m pip install --upgrade pip
        cd django_migration
        pip install -r requirements.txt
    
    - name: Run migrations
      env:
        DATABASE_URL: postgres://postgres:postgres@localhost:5432/the5hc_test
        SECRET_KEY: test-secret-key-for-ci
      run: |
        cd django_migration
        python manage.py migrate
    
    - name: Run tests with coverage
      env:
        DATABASE_URL: postgres://postgres:postgres@localhost:5432/the5hc_test
        SECRET_KEY: test-secret-key-for-ci
        DJANGO_SETTINGS_MODULE: the5hc.settings.test
      run: |
        cd django_migration
        pytest --cov=apps --cov-report=xml --cov-report=term-missing -v
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./django_migration/coverage.xml
        flags: unittests
        name: codecov-umbrella
        fail_ci_if_error: true
```

### Advanced Workflow with Matrix Testing

```yaml
name: Django CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      fail-fast: false
      matrix:
        os: [ubuntu-latest, macos-latest]
        python-version: ['3.10', '3.11', '3.12']
        django-version: ['4.2', '5.0']
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        cd django_migration
        pip install -r requirements.txt
        pip install "Django~=${{ matrix.django-version }}.0"
    
    - name: Run tests
      run: |
        cd django_migration
        pytest -v

  lint:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install ruff black isort mypy
    
    - name: Run linters
      run: |
        cd django_migration
        ruff check .
        black --check .
        isort --check-only .
        mypy apps/

  security:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Run security checks
      run: |
        pip install safety bandit
        cd django_migration
        safety check
        bandit -r apps/
```

## GitLab CI/CD

Create `.gitlab-ci.yml`:

```yaml
stages:
  - test
  - quality
  - deploy

variables:
  PIP_CACHE_DIR: "$CI_PROJECT_DIR/.cache/pip"
  POSTGRES_DB: the5hc_test
  POSTGRES_USER: postgres
  POSTGRES_PASSWORD: postgres
  DATABASE_URL: "postgres://postgres:postgres@postgres:5432/the5hc_test"

cache:
  paths:
    - .cache/pip
    - venv/

before_script:
  - apt-get update -qy
  - apt-get install -y python3-dev python3-pip postgresql-client
  - pip install virtualenv
  - virtualenv venv
  - source venv/bin/activate
  - cd django_migration
  - pip install -r requirements.txt

test:unit:
  stage: test
  services:
    - postgres:15
  script:
    - python manage.py migrate
    - pytest --cov=apps --cov-report=xml --cov-report=term
  coverage: '/(?i)total.*? (100(?:\.0+)?\%|[1-9]?\d(?:\.\d+)?\%)$/'
  artifacts:
    reports:
      coverage_report:
        coverage_format: cobertura
        path: coverage.xml

test:integration:
  stage: test
  services:
    - postgres:15
  script:
    - python manage.py migrate
    - pytest -m integration

quality:lint:
  stage: quality
  script:
    - pip install ruff black isort
    - ruff check .
    - black --check .
    - isort --check-only .

quality:security:
  stage: quality
  script:
    - pip install safety bandit
    - safety check
    - bandit -r apps/ -f json -o bandit_report.json
  artifacts:
    reports:
      sast: bandit_report.json
```

## Pre-commit Hooks

### Installation

```bash
pip install pre-commit
```

### Configuration

Create `.pre-commit-config.yaml`:

```yaml
repos:
  # Python code formatting
  - repo: https://github.com/psf/black
    rev: 23.12.0
    hooks:
      - id: black
        language_version: python3.11
        args: ['--line-length=88']

  # Import sorting
  - repo: https://github.com/pycqa/isort
    rev: 5.13.0
    hooks:
      - id: isort
        args: ['--profile=black']

  # Linting
  - repo: https://github.com/charliermarsh/ruff-pre-commit
    rev: v0.1.8
    hooks:
      - id: ruff
        args: ['--fix']

  # Security checks
  - repo: https://github.com/pycqa/bandit
    rev: 1.7.5
    hooks:
      - id: bandit
        args: ['-c', '.bandit']
        exclude: 'tests/'

  # Django specific
  - repo: local
    hooks:
      - id: django-check
        name: Django Check
        entry: bash -c 'cd django_migration && python manage.py check'
        language: system
        pass_filenames: false

      - id: django-migrations
        name: Check Django Migrations
        entry: bash -c 'cd django_migration && python manage.py makemigrations --check --dry-run'
        language: system
        pass_filenames: false

      - id: django-tests
        name: Django Tests
        entry: bash -c 'cd django_migration && pytest tests/ -x'
        language: system
        pass_filenames: false
        stages: [push]

  # YAML files
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: check-yaml
      - id: end-of-file-fixer
      - id: trailing-whitespace
      - id: check-added-large-files
      - id: check-merge-conflict
```

### Usage

```bash
# Install pre-commit hooks
pre-commit install

# Run manually on all files
pre-commit run --all-files

# Skip hooks temporarily
git commit --no-verify
```

## Docker Testing

### Test Dockerfile

Create `Dockerfile.test`:

```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    libpq-dev \
    gcc \
    gettext \
    libcairo2-dev \
    libpango1.0-dev \
    libgdk-pixbuf2.0-dev \
    libffi-dev \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements
COPY django_migration/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY django_migration/ .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=the5hc.settings.test

# Run tests
CMD ["pytest", "--cov=apps", "--cov-report=term-missing", "-v"]
```

### Docker Compose for Testing

Create `docker-compose.test.yml`:

```yaml
version: '3.8'

services:
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: the5hc_test
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5

  test:
    build:
      context: .
      dockerfile: Dockerfile.test
    depends_on:
      db:
        condition: service_healthy
    environment:
      DATABASE_URL: postgres://postgres:postgres@db:5432/the5hc_test
      SECRET_KEY: test-secret-key
    volumes:
      - ./django_migration:/app
    command: >
      sh -c "python manage.py migrate &&
             pytest --cov=apps --cov-report=xml --cov-report=term-missing -v"
```

### Running Docker Tests

```bash
# Build and run tests
docker-compose -f docker-compose.test.yml up --build

# Run specific test
docker-compose -f docker-compose.test.yml run test pytest apps/accounts/

# Clean up
docker-compose -f docker-compose.test.yml down -v
```

## Coverage Requirements

### Coverage Configuration

Create `.coveragerc`:

```ini
[run]
source = apps
omit = 
    */migrations/*
    */tests/*
    */test_*.py
    */__init__.py
    */admin.py
    */apps.py
    */factories.py
    venv/*
    */settings/*

[report]
precision = 2
show_missing = True
skip_covered = False

[html]
directory = htmlcov

[xml]
output = coverage.xml
```

### Enforce Coverage in CI

```yaml
# In GitHub Actions
- name: Check coverage threshold
  run: |
    cd django_migration
    coverage report --fail-under=80

# Or with pytest
- name: Run tests with coverage threshold
  run: |
    cd django_migration
    pytest --cov=apps --cov-fail-under=80
```

## Environment Setup

### Test Environment Variables

Create `.env.test`:

```bash
# Database
DATABASE_URL=postgres://postgres:postgres@localhost:5432/the5hc_test

# Django
SECRET_KEY=test-secret-key-for-ci-only
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1

# Testing
TESTING=True
DJANGO_SETTINGS_MODULE=the5hc.settings.test

# Disable external services
DISABLE_EMAIL=True
DISABLE_SMS=True
DISABLE_CACHE=True
```

### Secrets Management

```yaml
# GitHub Actions secrets
- name: Run tests
  env:
    SECRET_KEY: ${{ secrets.TEST_SECRET_KEY }}
    DATABASE_URL: ${{ secrets.TEST_DATABASE_URL }}
```

## Best Practices

### 1. Fast Feedback

```yaml
# Run quick checks first
jobs:
  quick-checks:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Check formatting
        run: black --check .
      - name: Check imports
        run: isort --check-only .
      
  full-tests:
    needs: quick-checks
    runs-on: ubuntu-latest
    # ... full test suite
```

### 2. Parallel Testing

```yaml
# Split tests across multiple jobs
test:
  strategy:
    matrix:
      app: [accounts, clients, assessments, sessions]
  steps:
    - name: Run app tests
      run: pytest apps/${{ matrix.app }}/
```

### 3. Caching Strategy

```yaml
# Cache dependencies
- uses: actions/cache@v3
  with:
    path: |
      ~/.cache/pip
      .pytest_cache
      .ruff_cache
    key: ${{ runner.os }}-${{ hashFiles('**/requirements*.txt') }}
```

### 4. Fail Fast Configuration

```yaml
# Stop on first failure in development
test:
  strategy:
    fail-fast: ${{ github.event_name == 'pull_request' }}
```

### 5. Notification Setup

```yaml
# Slack notification on failure
- name: Notify Slack on Failure
  if: failure()
  uses: 8398a7/action-slack@v3
  with:
    status: ${{ job.status }}
    text: 'Tests failed in ${{ github.repository }}'
  env:
    SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK }}
```

## Testing Commands Reference

```bash
# Local testing
cd django_migration
pytest                          # Run all tests
pytest -x                       # Stop on first failure
pytest --lf                     # Run last failed
pytest -k "test_login"          # Run specific tests
pytest --markers                # Show available markers

# CI/CD testing
pytest --cov=apps --cov-report=xml    # Generate coverage report
pytest --junit-xml=report.xml          # Generate JUnit report
pytest --maxfail=5                     # Stop after 5 failures

# Performance testing
pytest --durations=10           # Show 10 slowest tests
pytest -n auto                  # Run in parallel
```

## Troubleshooting

### Common CI/CD Issues

1. **Database connection errors**
   - Ensure service health checks pass
   - Check DATABASE_URL format
   - Verify network connectivity

2. **Missing system dependencies**
   - Add required packages to install step
   - Use appropriate base image

3. **Locale errors**
   ```yaml
   - name: Set up locale
     run: |
       sudo locale-gen ko_KR.UTF-8
       export LC_ALL=ko_KR.UTF-8
   ```

4. **Memory issues**
   ```yaml
   # Increase Node memory for asset building
   env:
     NODE_OPTIONS: "--max_old_space_size=4096"
   ```

5. **Timeout issues**
   ```yaml
   - name: Run tests
     timeout-minutes: 30  # Increase timeout
   ```

## Summary

A well-configured CI/CD pipeline ensures:
- ✅ Code quality through automated checks
- ✅ Consistent test execution across environments
- ✅ Fast feedback for developers
- ✅ Protection of main branches
- ✅ Automated deployment readiness

Keep your CI/CD configuration updated as your project evolves!