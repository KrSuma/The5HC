# MCQ Management Commands Guide

This document provides comprehensive guidance on using the Django management commands for MCQ (Multiple Choice Questions) functionality in The5HC system.

## Overview

The MCQ management commands provide tools for:
- Loading default questions from files
- Exporting questions for backup or sharing
- Validating data integrity
- Generating response statistics and insights

## Available Commands

### 1. load_mcq_questions

Load MCQ questions from JSON or CSV files into the database.

#### Basic Usage
```bash
# Load default questions
python manage.py load_mcq_questions

# Load from specific file
python manage.py load_mcq_questions --file questions.json

# Load CSV format
python manage.py load_mcq_questions --file questions.csv --format csv

# Clear existing questions before loading
python manage.py load_mcq_questions --clear

# Preview what would be loaded (dry run)
python manage.py load_mcq_questions --dry-run
```

#### File Locations
The command looks for files in these locations (in order):
1. `{BASE_DIR}/data/{filename}`
2. `{BASE_DIR}/fixtures/{filename}`
3. `{BASE_DIR}/apps/assessments/fixtures/{filename}`
4. Current directory

#### JSON Format
```json
[
  {
    "category": {
      "name": "Knowledge Assessment",
      "name_ko": "지식 평가",
      "weight": 0.15,
      "order": 1,
      "description": "Fitness knowledge assessment",
      "description_ko": "체력 지식 평가"
    },
    "question_text": "What is the recommended frequency for strength training?",
    "question_text_ko": "근력 운동 권장 빈도는?",
    "question_type": "single",
    "is_required": true,
    "points": 5,
    "help_text": "According to fitness guidelines",
    "help_text_ko": "체력 가이드라인에 따르면",
    "order": 1,
    "is_active": true,
    "choices": [
      {
        "choice_text": "2-3 times per week",
        "choice_text_ko": "주 2-3회",
        "points": 5,
        "risk_factor": "",
        "order": 1,
        "is_correct": true
      }
    ]
  }
]
```

#### CSV Format
| Column | Description | Required |
|--------|-------------|----------|
| category_name | Category English name | Yes |
| category_name_ko | Category Korean name | No |
| category_weight | Category weight (0.0-1.0) | No |
| category_order | Category order | No |
| question_text | Question English text | Yes |
| question_text_ko | Question Korean text | No |
| question_type | single/multiple/scale/text | No |
| is_required | True/False | No |
| points | Question points | No |
| help_text | Help text English | No |
| help_text_ko | Help text Korean | No |
| order | Question order | No |
| is_active | True/False | No |
| choice_1_text to choice_5_text | Choice texts | No |
| choice_1_text_ko to choice_5_text_ko | Choice Korean texts | No |
| choice_1_points to choice_5_points | Choice points | No |
| choice_1_risk_factor to choice_5_risk_factor | Risk factors | No |
| choice_1_is_correct to choice_5_is_correct | Correct flags | No |

### 2. export_mcq_questions

Export MCQ questions to various formats for backup or sharing.

#### Basic Usage
```bash
# Export all questions to JSON
python manage.py export_mcq_questions

# Export to CSV
python manage.py export_mcq_questions --format csv --output questions.csv

# Export specific category
python manage.py export_mcq_questions --category "Knowledge Assessment"

# Export only active questions
python manage.py export_mcq_questions --active-only

# Include response statistics
python manage.py export_mcq_questions --include-responses

# Pretty print JSON
python manage.py export_mcq_questions --pretty
```

#### Export Formats

**JSON**: Complete structured format with all relationships
```bash
python manage.py export_mcq_questions --format json --output backup.json
```

**CSV**: Flat format suitable for Excel editing
```bash
python manage.py export_mcq_questions --format csv --output questions.csv
```

**YAML**: Human-readable format for version control
```bash
python manage.py export_mcq_questions --format yaml --output questions.yml
```

### 3. validate_mcq_data

Validate MCQ data integrity and optionally fix common issues.

#### Basic Usage
```bash
# Validate all data
python manage.py validate_mcq_data

# Fix issues automatically
python manage.py validate_mcq_data --fix

# Check dependency chains
python manage.py validate_mcq_data --check-dependencies

# Validate specific category
python manage.py validate_mcq_data --category "Knowledge Assessment"

# Verbose output
python manage.py validate_mcq_data --verbose
```

#### Validation Checks

**Categories**:
- Duplicate category names
- Invalid weights (not between 0-1)
- Total weights not summing to 1.0

**Questions**:
- Questions without choices (for choice-type questions)
- Invalid question types
- Negative points
- Duplicate orders within categories

**Choices**:
- Single-choice questions with multiple correct answers
- Negative points in choices
- Duplicate choice orders within questions

**Dependencies**:
- Circular dependencies
- Broken dependency answers
- Cross-category dependencies (warning)

**Responses**:
- Orphaned responses (question deleted)
- Invalid choice selections

### 4. mcq_statistics

Generate comprehensive statistics and insights about MCQ responses.

#### Basic Usage
```bash
# Generate all statistics
python manage.py mcq_statistics

# Filter by date range
python manage.py mcq_statistics --start-date 2025-01-01 --end-date 2025-12-31

# Filter by trainer
python manage.py mcq_statistics --trainer 5

# Filter by category
python manage.py mcq_statistics --category "Knowledge Assessment"

# Export to CSV
python manage.py mcq_statistics --export stats.csv

# Detailed question-level statistics
python manage.py mcq_statistics --detailed
```

#### Statistics Generated

**Overview**:
- Total assessments and MCQ completion rates
- Average responses per assessment
- MCQ score averages by category

**Category Statistics**:
- Response rates by category
- Average scores and points earned
- Question count and activity metrics

**Question Analysis**:
- Response counts and patterns
- Choice distribution
- Discrimination index (question quality metric)
- Difficulty analysis

**Response Patterns**:
- Completion rates by question type
- High skip-rate questions
- Response consistency metrics

**Quality Metrics**:
- MCQ-Physical score alignment
- Question difficulty distribution
- Internal consistency indicators

## Best Practices

### Data Loading
1. **Always backup** before loading new questions with `--clear`
2. **Use dry-run** first to preview changes
3. **Validate data** after loading
4. **Test thoroughly** in development before production

### Data Management
1. **Regular exports** for backup purposes
2. **Version control** for question files
3. **Validate periodically** to catch data drift
4. **Monitor statistics** to identify issues

### Quality Assurance
1. **Review discrimination indexes** - aim for > 0.3
2. **Balance difficulty** - avoid too many very easy/hard questions
3. **Check skip rates** - investigate questions > 20% skip rate
4. **Monitor completion rates** - should be > 80% for required questions

## Sample Workflows

### Initial Setup
```bash
# 1. Load initial questions
python manage.py load_mcq_questions --file initial_questions.json

# 2. Validate the data
python manage.py validate_mcq_data --verbose

# 3. Export for backup
python manage.py export_mcq_questions --output backup_$(date +%Y%m%d).json
```

### Regular Maintenance
```bash
# Weekly: Check data integrity
python manage.py validate_mcq_data

# Monthly: Generate statistics
python manage.py mcq_statistics --detailed --export monthly_stats.csv

# Quarterly: Full backup
python manage.py export_mcq_questions --include-responses --output quarterly_backup.json
```

### Troubleshooting
```bash
# Check for specific issues
python manage.py validate_mcq_data --check-dependencies --verbose

# Fix common problems
python manage.py validate_mcq_data --fix

# Analyze question quality
python manage.py mcq_statistics --detailed
```

## Error Handling

### Common Errors

**File not found**: Check file path and locations
```bash
python manage.py load_mcq_questions --file /full/path/to/questions.json
```

**Invalid JSON/CSV format**: Validate file format
```bash
# Test with small sample first
python manage.py load_mcq_questions --file sample.json --dry-run
```

**Database constraint errors**: Check data integrity
```bash
python manage.py validate_mcq_data --verbose
```

**Permission errors**: Check Django permissions and database access

### Recovery Procedures

1. **Backup current state**:
   ```bash
   python manage.py export_mcq_questions --output emergency_backup.json
   ```

2. **Clear corrupted data** (if necessary):
   ```bash
   python manage.py load_mcq_questions --clear --file clean_questions.json
   ```

3. **Validate and fix**:
   ```bash
   python manage.py validate_mcq_data --fix
   ```

## Integration with Admin Interface

The management commands complement the Django admin interface:

- **Admin**: Interactive editing, single question management
- **Commands**: Bulk operations, automation, validation

Use admin for daily editing and commands for:
- Initial setup
- Bulk imports/exports
- Data validation
- Statistics generation
- Automated maintenance

## Performance Considerations

### Large Datasets
- Use `--active-only` for exports when appropriate
- Batch operations are automatically used
- Database queries are optimized with select_related/prefetch_related

### Production Usage
- Run exports during low-traffic periods
- Use `--dry-run` for testing
- Monitor database performance during imports
- Consider backup timing

## Security Notes

- Commands respect Django permissions
- No sensitive data is exposed in exports
- Validation doesn't modify data unless `--fix` is used
- All operations are logged for audit trails