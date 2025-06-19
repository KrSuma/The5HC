# Multiple Choice Questions (MCQ) Implementation Plan for The5HC

## Overview

This document outlines the missing components from the `additional-questions.md` plan that need to be implemented to add a comprehensive Multiple Choice Questions system to The5HC Fitness Assessment System.

## Current State vs. Target State

### Currently Implemented:
- Physical Assessment Tests (27 test fields)
- Movement Quality Tracking (FMS scoring)
- Risk Scoring System (0-100 scale)
- Percentile Rankings with normative data
- Test Variations Support
- Database-backed Test Standards

### Target State:
- Complete MCQ system integrated with existing assessments
- Knowledge, Lifestyle, and Readiness evaluations
- Comprehensive scoring combining physical (60%) and MCQ (40%) results
- Enhanced risk assessment with lifestyle factors
- Multi-language support (Korean/English)
- Real-time scoring and conditional questions
- Updated PDF reports with MCQ results

## Implementation Phases

### Phase 1: Database Schema Design (2-3 days)

**Missing Components:**
1. Create `QuestionCategory` model
   - name, name_ko, description, weight, order, is_active
   - Weight factor for scoring (0.0-1.0)

2. Create `MultipleChoiceQuestion` model
   - category, question_text, question_text_ko
   - question_type (single, multiple, scale)
   - points, is_required, help_text
   - Conditional display (depends_on, depends_on_answer)

3. Create `QuestionChoice` model
   - question, choice_text, choice_text_ko
   - points, is_correct, order
   - Risk factors (contributes_to_risk, risk_weight)

4. Create `QuestionResponse` model
   - assessment, question, selected_choices
   - response_text, points_earned

5. Update `Assessment` model with new fields:
   - knowledge_score (0-100)
   - lifestyle_score (0-100)
   - readiness_score (0-100)
   - comprehensive_score (0-100)

### Phase 2: Scoring System Integration (2 days)

**Missing Components:**
1. Create `MCQScoringEngine` class
   - calculate_category_score()
   - calculate_comprehensive_score()
   - calculate_mcq_risk_factors()

2. Scoring weights implementation:
   - Physical Assessment: 60%
   - Knowledge Assessment: 15%
   - Lifestyle Assessment: 15%
   - Readiness Assessment: 10%

3. Update Assessment.calculate_scores() method
   - Integrate MCQ scoring
   - Calculate comprehensive score
   - Add MCQ risk factors to existing risk assessment

### Phase 3: Forms and UI Implementation (3-4 days)

**Missing Components:**
1. Create `QuestionResponseForm` for dynamic MCQ rendering
   - Single choice (radio buttons)
   - Multiple choice (checkboxes)
   - Scale/rating questions

2. Update `AssessmentForm` to include MCQ forms
   - Dynamic field generation
   - Conditional question handling
   - Validation logic

3. HTMX/Alpine.js integration
   - Progressive disclosure
   - Real-time validation
   - Score preview

### Phase 4: Templates and UI Components (2-3 days)

**Missing Components:**
1. Create `mcq_section.html` template
   - Question display by category
   - Conditional question show/hide
   - Real-time score preview

2. Alpine.js components:
   - mcqHandler() for client-side logic
   - Score calculation preview
   - Conditional display logic

3. Update assessment form templates
   - Integrate MCQ section
   - Progress indicators
   - Score visualization

### Phase 5: API Implementation (2 days)

**Missing Components:**
1. Create `MultipleChoiceQuestionViewSet`
   - List questions by category
   - Validate responses
   - Calculate scores

2. Create MCQ serializers:
   - QuestionCategorySerializer
   - MultipleChoiceQuestionSerializer
   - QuestionChoiceSerializer
   - MCQResponseSerializer

3. API endpoints:
   - `/api/v1/mcq/` - List all questions
   - `/api/v1/mcq/by-category/` - Questions grouped by category
   - `/api/v1/mcq/validate-responses/` - Validate and score responses

### Phase 6: Admin Interface (1 day)

**Missing Components:**
1. QuestionCategoryAdmin
   - List display with weight and order
   - Inline editing

2. MultipleChoiceQuestionAdmin
   - Question preview
   - Choice inline editing
   - Conditional display configuration

3. Import/export functionality
   - Bulk question management
   - CSV import/export

### Phase 7: Management Commands (1 day)

**Missing Components:**
1. Create `load_mcq_questions` command
   - Load default categories
   - Load sample questions for each category
   - Set up scoring thresholds

2. Sample questions to load:
   - Knowledge: Exercise form, nutrition, recovery, injury prevention
   - Lifestyle: Sleep, stress, diet, hydration, activity levels
   - Readiness: Current pain, recovery status, motivation, time availability

### Phase 8: Testing Implementation (2 days)

**Missing Components:**
1. Model tests:
   - MCQ model relationships
   - Scoring calculations
   - Risk factor extraction

2. Form tests:
   - Dynamic form generation
   - Validation logic
   - Conditional questions

3. API tests:
   - Endpoint functionality
   - Response validation
   - Score calculation

4. Integration tests:
   - Full assessment with MCQ
   - Comprehensive scoring
   - PDF generation

### Phase 9: PDF Report Updates (1 day)

**Missing Components:**
1. Update report generation service
   - Include MCQ scores
   - Group responses by category
   - Add comprehensive score section

2. Update report templates:
   - MCQ results section
   - Score summary table
   - Detailed response display

3. Visual enhancements:
   - Score comparison charts
   - Category breakdowns
   - Risk factor highlighting

### Phase 10: Migration and Deployment (1 day)

**Missing Components:**
1. Create database migrations
2. Test migration rollback/forward
3. Update deployment documentation
4. Load initial question data
5. Verify production deployment

## Question Categories and Examples

### Knowledge Assessment (15% weight)
- Exercise form and technique
- Basic nutrition principles
- Recovery and rest importance
- Injury prevention strategies
- Training principles

### Lifestyle Assessment (15% weight)
- Sleep quality and duration (7-9 hours optimal)
- Stress management techniques
- Dietary habits and meal timing
- Hydration levels (2-3L daily)
- Physical activity outside training

### Readiness Assessment (10% weight)
- Current pain or discomfort levels
- Recovery from previous workouts
- Mental/emotional readiness
- Time availability for training
- Motivation and goal clarity

## Technical Considerations

### Database Performance
- Index question lookups by category and order
- Cache frequently accessed questions
- Optimize response queries with select_related/prefetch_related

### UI/UX Considerations
- Mobile-responsive MCQ forms
- Progress saving for long assessments
- Clear Korean/English language toggle
- Intuitive conditional question flow

### Security Considerations
- Validate all MCQ responses server-side
- Prevent score manipulation
- Audit trail for assessment modifications

## Success Metrics

1. **Functionality**
   - All MCQ types working correctly
   - Accurate score calculations
   - Proper risk factor integration

2. **Performance**
   - Page load time < 2 seconds
   - Real-time score preview < 100ms
   - Efficient database queries

3. **User Experience**
   - Intuitive question flow
   - Clear progress indicators
   - Helpful validation messages

4. **Data Quality**
   - Comprehensive client evaluation
   - Actionable insights for trainers
   - Trackable progress over time

## Implementation Priority

1. **High Priority**
   - Database models (Phase 1)
   - Core scoring system (Phase 2)
   - Basic forms and UI (Phase 3)
   - Essential templates (Phase 4)

2. **Medium Priority**
   - API endpoints (Phase 5)
   - Testing suite (Phase 8)
   - PDF report updates (Phase 9)

3. **Lower Priority**
   - Admin interface (Phase 6)
   - Management commands (Phase 7)
   - Advanced UI features

## Estimated Timeline

- **Week 1**: Phases 1-2 (Database and Scoring)
- **Week 2**: Phases 3-4 (Forms and UI)
- **Week 3**: Phases 5-8 (API, Admin, Testing)
- **Week 4**: Phases 9-10 (Reports and Deployment)

Total: 4 weeks for complete implementation

## Next Steps

1. Review and approve this implementation plan
2. Create detailed technical specifications for Phase 1
3. Set up development branch for MCQ feature
4. Begin database model implementation
5. Create initial migration files