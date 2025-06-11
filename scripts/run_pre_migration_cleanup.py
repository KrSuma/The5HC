#!/usr/bin/env python
"""
Run pre-migration cleanup without user prompts
"""
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from pre_migration_cleanup import PreMigrationCleanup

# Find database path
project_root = Path(__file__).parent.parent.parent
db_path = project_root / 'data' / 'fitness_assessment.db'

if not db_path.exists():
    db_path = project_root / 'fitness_assessment.db'

if not db_path.exists():
    print(f"❌ Database not found at: {db_path}")
    sys.exit(1)

print(f"Database: {db_path}")
print("\nRunning pre-migration cleanup...")

# Run cleanup
cleanup = PreMigrationCleanup(str(db_path))
success = cleanup.run()

sys.exit(0 if success else 1)