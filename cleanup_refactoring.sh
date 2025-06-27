#!/bin/bash

# The5HC Refactoring Cleanup Script
# This script removes unused refactoring files that are not in production
# Date: 2025-06-26

echo "The5HC Refactoring Cleanup Script"
echo "================================="
echo "This will remove unused refactoring files that are not in production."
echo ""

# Ask for confirmation
read -p "Are you sure you want to proceed? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]
then
    echo "Cleanup cancelled."
    exit 1
fi

echo ""
echo "Starting cleanup..."
echo ""

# 1. Remove test scripts in root directory
echo "1. Removing test scripts in root..."
rm -f test_form_refactoring_deployment.py
rm -f test_form_browser.py
rm -f test_form_deployment.py
rm -f fix_form_initialization.py
rm -f test_refactored_forms.py
rm -f test_template_optimization.py
rm -f validate_refactoring.py
rm -f test_app_status.py

# 2. Remove unused refactored assessments files
echo "2. Removing unused assessment refactoring files..."
rm -f apps/assessments/forms/refactored_forms.py
rm -f apps/assessments/refactored_models.py
rm -f apps/assessments/example_migration.py
rm -f apps/assessments/views_optimized.py
rm -f apps/assessments/templatetags/assessment_refactored_tags.py
rm -f apps/assessments/managers.py
rm -f apps/assessments/services.py

# 3. Remove unused refactored client files
echo "3. Removing unused client refactoring files..."
rm -f apps/clients/views_refactored.py
rm -f apps/clients/views_with_mixins.py
rm -f apps/clients/urls_test.py

# 4. Remove refactored templates
echo "4. Removing unused refactored templates..."
rm -f templates/assessments/assessment_form_refactored.html
rm -f templates/assessments/assessment_form_refactored_content.html
rm -f templates/assessments/assessment_list_optimized.html
rm -f templates/assessments/assessment_detail_optimized.html
rm -f templates/assessments/assessment_detail_optimized_content.html
rm -f templates/assessments/components/test_display.html
rm -f templates/clients/client_list_optimized.html
rm -f templates/components/timer_examples.html

# 5. Remove refactored JavaScript files
echo "5. Removing unused JavaScript files..."
rm -f static/js/assessment-form-refactored.js
rm -f static/js/app-refactored.js
rm -f static/js/app.js.backup
rm -f static/js/timer-components.js
rm -f static/css/timer-components.css
rm -rf staticfiles/js/app.js.backup

# 6. Remove example/test files
echo "6. Removing example and test files..."
rm -f apps/accounts/factories_example.py
rm -f apps/accounts/test_views_pytest_example.py
rm -f apps/core/mixins/examples.py
rm -f apps/core/mixins/model_examples.py
rm -f apps/core/services/examples.py

# 7. Archive old documentation (don't delete, just move)
echo "7. Archiving old refactoring documentation..."
mkdir -p docs/archive/refactoring
mv -f docs/REFACTORING_*.md docs/archive/refactoring/ 2>/dev/null || true
mv -f docs/DUAL_TEMPLATE_*.md docs/archive/refactoring/ 2>/dev/null || true
mv -f docs/JAVASCRIPT_REFACTORING_GUIDE.md docs/archive/refactoring/ 2>/dev/null || true
mv -f docs/SERVICE_LAYER_IMPLEMENTATION.md docs/archive/refactoring/ 2>/dev/null || true
mv -f docs/PHASE2_ASSESSMENT_REFACTORING_COMPLETE.md docs/archive/refactoring/ 2>/dev/null || true

# 8. Archive old refactoring logs
echo "8. Archiving refactoring logs..."
mkdir -p logs/archive/refactoring
mv -f logs/feature/*REFACTORING*.md logs/archive/refactoring/ 2>/dev/null || true
mv -f logs/feature/FORMS_REFACTORING_*.md logs/archive/refactoring/ 2>/dev/null || true
mv -f logs/feature/JAVASCRIPT_REFACTORING_*.md logs/archive/refactoring/ 2>/dev/null || true
mv -f logs/feature/TEMPLATE_OPTIMIZATION_*.md logs/archive/refactoring/ 2>/dev/null || true

# 9. Check for migrations (DO NOT DELETE - just warn)
echo ""
echo "⚠️  WARNING: Found refactoring migrations that need manual review:"
echo "   - apps/assessments/migrations/0014_add_refactored_models.py"
echo "   - apps/assessments/migrations/0015_migrate_to_refactored_models.py"
echo ""
echo "   These migrations should be reviewed before deletion."
echo "   Run 'python manage.py showmigrations' to check if they're applied."
echo ""

# 10. Summary
echo "Cleanup Summary:"
echo "================"
echo "✅ Removed test scripts from root directory"
echo "✅ Removed unused refactored view files"
echo "✅ Removed unused refactored form files"
echo "✅ Removed unused refactored templates"
echo "✅ Removed unused JavaScript files"
echo "✅ Removed example/test files"
echo "✅ Archived old documentation to docs/archive/refactoring/"
echo "✅ Archived old logs to logs/archive/refactoring/"
echo ""
echo "⚠️  Kept: apps/core/ (good infrastructure for future use)"
echo "⚠️  Kept: Migrations 0014 and 0015 (need manual review)"
echo ""

# Count cleaned files
CLEANED_COUNT=$(find . -name "*.pyc" -o -name "__pycache__" | wc -l)
echo "Additionally found $CLEANED_COUNT Python cache files that could be cleaned."
echo ""

# Final message
echo "Cleanup complete! The project now contains only production code."
echo "To further clean Python cache files, run: find . -name '*.pyc' -delete && find . -name '__pycache__' -type d -delete"
echo ""
echo "Next steps:"
echo "1. Review migrations 0014 and 0015"
echo "2. Commit these changes: git add -A && git commit -m 'Clean up unused refactoring files'"
echo "3. Test that everything still works: python manage.py runserver"