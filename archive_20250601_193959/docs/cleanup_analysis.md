# Directory Cleanup Analysis

## Files to Keep (Essential)

### Core Application Files
- `main_improved.py` - New secure main application
- `config.py` - Centralized configuration
- `requirements.txt` - Dependencies

### UI Components
- `ui_pages.py` - UI pages (still in use)
- `improved_assessment_page.py` - Assessment form
- `simplified_add_client.py` - Client addition page

### Business Logic
- `improved_service_layer.py` - New secure service layer
- `improved_assessment_scoring.py` - Scoring logic
- `improved_recommendations.py` - Recommendation engine
- `improved_pdf_generator.py` - PDF generation

### Security & Infrastructure
- `secure_db_utils.py` - Secure database operations
- `session_manager.py` - Session management
- `logging_config.py` - Logging configuration
- `database_layer.py` - Database abstraction
- `cache_manager.py` - Caching system

### Resources
- `NanumGothic.ttf` - Korean font
- `NanumGothicBold.ttf` - Korean font bold
- `fitness_assessment.db` - Main database
- `README.md` - Documentation

### Tests
- `test_assessment_scoring.py` - Scoring tests
- `test_security.py` - Security tests
- `test_database_layer.py` - Database tests
- `test_cache_performance.py` - Cache tests

## Files to Archive/Remove

### Deprecated Files (replaced by improved versions)
- `main.py` - Old main file (replaced by main_improved.py)
- `service_layer.py` - Old service layer (replaced by improved_service_layer.py)
- `improved_db_utils.py` - Old database utils (replaced by secure_db_utils.py)

### Migration/Temporary Files
- `migrate_to_improved.py` - One-time migration script
- `simple_migration.py` - Simplified migration script
- `update_imports.py` - Import update script
- `service_layer_bridge.py` - Temporary bridge for compatibility

### Backup Files
- `fitness_assessment.db.backup_20250601_192859` - Database backup

### Documentation (can move to docs folder)
- `MIGRATION_SUMMARY.md` - Migration documentation

## Recommended Directory Structure

```
The5HC/
├── app/
│   ├── main.py (renamed from main_improved.py)
│   ├── config.py
│   ├── pages/
│   │   ├── ui_pages.py
│   │   ├── assessment_page.py
│   │   └── add_client_page.py
│   ├── services/
│   │   ├── auth_service.py
│   │   ├── client_service.py
│   │   └── assessment_service.py
│   ├── core/
│   │   ├── database.py
│   │   ├── security.py
│   │   ├── session.py
│   │   ├── logging.py
│   │   └── cache.py
│   └── utils/
│       ├── scoring.py
│       ├── recommendations.py
│       └── pdf_generator.py
├── tests/
│   ├── test_scoring.py
│   ├── test_security.py
│   ├── test_database.py
│   └── test_cache.py
├── resources/
│   ├── fonts/
│   │   ├── NanumGothic.ttf
│   │   └── NanumGothicBold.ttf
│   └── data/
│       └── fitness_assessment.db
├── docs/
│   ├── README.md
│   └── MIGRATION_GUIDE.md
├── backups/
│   └── [backup files]
└── requirements.txt
```