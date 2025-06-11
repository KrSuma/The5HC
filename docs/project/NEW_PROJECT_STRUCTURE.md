# The5HC - New Project Structure (Post-Cleanup)

**Date**: 2025-01-11
**Purpose**: Visualize the clean Django-only project structure after Streamlit removal

## Current Structure (Before Cleanup)

```
The5HC/ (Mixed Streamlit + Django)
├── Streamlit Files (TO DELETE)
│   ├── main.py
│   ├── run_app.sh
│   ├── src/ (50+ files)
│   ├── config/
│   ├── scripts/
│   ├── tests/
│   └── data/
├── Django Project
│   └── django_migration/
└── Shared Resources
    ├── docs/
    ├── assets/
    └── logs/
```

## New Structure (After Cleanup)

### Option 1: Keep Django in Subdirectory (Minimal Change)

```
The5HC/
├── django_migration/              # Main Django application
│   ├── apps/                     # Django apps (7 modules)
│   │   ├── accounts/            # User authentication
│   │   ├── analytics/           # Analytics (placeholder)
│   │   ├── api/                 # RESTful API
│   │   ├── assessments/         # Fitness assessments
│   │   ├── clients/             # Client management
│   │   ├── reports/             # PDF generation
│   │   ├── sessions/            # Session management
│   │   └── trainers/            # Trainer management
│   ├── locale/                  # Korean translations
│   │   └── ko/LC_MESSAGES/      # Compiled translations
│   ├── logs/                    # All project logs (consolidated)
│   ├── media/                   # User uploads
│   ├── scripts/                 # Django utility scripts
│   ├── static/                  # CSS, JS, fonts
│   ├── templates/               # HTML templates
│   ├── the5hc/                  # Django settings
│   ├── manage.py               # Django CLI
│   ├── requirements.txt        # Python dependencies
│   ├── pytest.ini              # Test configuration
│   ├── the5hc_dev             # SQLite database
│   └── README.md              # Django documentation
├── assets/                     # Shared assets
│   └── fonts/                  # PDF generation fonts
│       ├── NanumGothic.ttf
│       └── NanumGothicBold.ttf
├── docs/                       # Project documentation
│   ├── kb/                     # Knowledge base
│   │   ├── build/             # Build commands
│   │   ├── code-style/        # Code guidelines
│   │   ├── django/            # Django details
│   │   ├── project-notes/     # Project specifics
│   │   ├── troubleshooting/   # Troubleshooting
│   │   └── workflow/          # Workflows
│   ├── archive/               # Historical docs
│   │   └── streamlit-migration/
│   ├── API_DOCUMENTATION.md
│   ├── DEPLOYMENT_GUIDE.md
│   ├── PROJECT_STRUCTURE.md
│   └── SYSTEM_ARCHITECTURE.md
├── deployment/                # Deployment configs
│   ├── Procfile              # Heroku config
│   ├── runtime.txt           # Python version
│   └── nginx.conf            # Production server
├── .github/                  # GitHub configs
│   └── workflows/            # CI/CD pipelines
├── README.md                 # Main documentation
├── CLAUDE.md                 # AI assistant KB
├── LICENSE                   # Project license
└── .gitignore               # Git ignore rules
```

### Option 2: Promote Django to Root (Cleaner Structure)

```
The5HC/
├── apps/                        # Django applications
│   ├── accounts/               # User authentication
│   ├── analytics/              # Analytics dashboard
│   ├── api/                    # RESTful API
│   ├── assessments/            # Fitness assessments
│   ├── clients/                # Client management
│   ├── reports/                # PDF generation
│   ├── sessions/               # Session tracking
│   └── trainers/               # Trainer profiles
├── locale/                     # Internationalization
│   └── ko/LC_MESSAGES/         # Korean translations
├── media/                      # User uploads
│   ├── assessments/            # Assessment files
│   └── reports/                # Generated PDFs
├── static/                     # Static assets
│   ├── css/                    # Stylesheets
│   ├── js/                     # JavaScript
│   └── fonts/                  # Web fonts
├── templates/                  # Django templates
│   ├── base.html              # Base template
│   ├── components/            # Reusable components
│   └── [app_templates]/       # App-specific
├── the5hc/                    # Django project settings
│   ├── __init__.py
│   ├── settings/              # Modular settings
│   │   ├── base.py
│   │   ├── development.py
│   │   ├── production.py
│   │   └── test.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── assets/                    # Non-web assets
│   └── fonts/                 # PDF fonts
├── docs/                      # Documentation
│   ├── api/                   # API docs
│   ├── deployment/            # Deploy guides
│   ├── development/           # Dev guides
│   └── archive/               # Historical
├── logs/                      # Application logs
├── scripts/                   # Utility scripts
│   ├── backup_db.py
│   └── generate_fixtures.py
├── tests/                     # Test suite
│   ├── conftest.py
│   └── fixtures/
├── manage.py                  # Django CLI
├── requirements/              # Modular requirements
│   ├── base.txt
│   ├── development.txt
│   ├── production.txt
│   └── test.txt
├── pytest.ini                 # Test config
├── .env.example              # Environment template
├── Procfile                  # Heroku config
├── runtime.txt               # Python version
├── README.md                 # Project docs
├── CLAUDE.md                 # AI assistant KB
├── LICENSE
└── .gitignore
```

## Benefits of Each Option

### Option 1: Minimal Change
- ✅ Less work to implement
- ✅ Git history preserved better
- ✅ Familiar structure maintained
- ❌ "migration" in path is misleading
- ❌ Nested structure is deeper

### Option 2: Clean Root
- ✅ Cleaner, more standard Django layout
- ✅ No "migration" terminology
- ✅ Easier to navigate
- ✅ Better for new developers
- ❌ More work to restructure
- ❌ Git history more complex

## Recommended Structure Details

### Key Directories

```
apps/                    # Business logic
├── Each app contains:
│   ├── models.py       # Data models
│   ├── views.py        # View logic
│   ├── urls.py         # URL routing
│   ├── forms.py        # Form definitions
│   ├── admin.py        # Admin interface
│   ├── tests/          # App tests
│   ├── factories.py    # Test factories
│   └── migrations/     # DB migrations

templates/              # UI templates
├── base.html          # Master template
├── includes/          # Partial templates
│   ├── navbar.html
│   ├── footer.html
│   └── messages.html
└── [app_name]/        # App templates
    ├── list.html
    ├── detail.html
    └── form.html

static/                # Frontend assets
├── css/
│   └── styles.css    # Custom styles
├── js/
│   └── app.js        # Custom JS
└── vendor/           # Third-party
    ├── htmx.min.js
    └── alpine.min.js
```

## File Count Comparison

### Before Cleanup
- Total files: ~400+
- Streamlit files: ~100
- Django files: ~250
- Shared/docs: ~50

### After Cleanup
- Total files: ~300
- Django files: ~250
- Documentation: ~30
- Configuration: ~20

## Migration Commands

### If choosing Option 2 (Promote to Root):

```bash
# After running cleanup_streamlit.sh
cd The5HC/

# Move Django to root
mv django_migration/* .
mv django_migration/.* . 2>/dev/null

# Remove empty directory
rmdir django_migration/

# Update any absolute imports
find . -name "*.py" -exec sed -i 's/django_migration\.//' {} \;

# Update settings paths
# Update documentation
# Commit changes
```

## Conclusion

**Recommendation**: Start with Option 1 (minimal change) for safety, then consider moving to Option 2 in a separate phase after everything is stable. This allows for:

1. Safe cleanup of Streamlit first
2. Verification that nothing breaks
3. Optional restructuring later
4. Clear git history for each phase