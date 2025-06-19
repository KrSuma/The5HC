# MCQ Phase 5: API Implementation Planning

**Created**: 2025-06-19
**Author**: Claude
**Status**: Planning Document

## Overview

Phase 5 focuses on creating a comprehensive RESTful API for the MCQ system, enabling integration with mobile applications, third-party systems, and providing programmatic access to MCQ functionality.

## Objectives

1. Create RESTful endpoints for all MCQ operations
2. Implement proper serializers with validation
3. Add authentication and permission controls
4. Create comprehensive API documentation
5. Enable batch operations for efficiency

## API Endpoints Design

### 1. Question Categories
```
GET    /api/v1/mcq/categories/                 # List all categories
GET    /api/v1/mcq/categories/{id}/            # Get category details
GET    /api/v1/mcq/categories/{id}/questions/  # Get questions in category
```

### 2. Questions
```
GET    /api/v1/mcq/questions/                  # List all questions (paginated)
GET    /api/v1/mcq/questions/{id}/             # Get question details
GET    /api/v1/mcq/questions/search/           # Search questions
POST   /api/v1/mcq/questions/validate/         # Validate answer
```

### 3. Assessment MCQ Operations
```
GET    /api/v1/assessments/{id}/mcq/           # Get MCQ status
POST   /api/v1/assessments/{id}/mcq/responses/ # Submit responses
PATCH  /api/v1/assessments/{id}/mcq/responses/ # Update responses
GET    /api/v1/assessments/{id}/mcq/results/   # Get results
DELETE /api/v1/assessments/{id}/mcq/responses/ # Clear responses
```

### 4. Batch Operations
```
POST   /api/v1/mcq/responses/batch/            # Submit multiple responses
GET    /api/v1/mcq/questions/batch/            # Get multiple questions
```

### 5. Analytics
```
GET    /api/v1/mcq/analytics/category-scores/  # Average scores by category
GET    /api/v1/mcq/analytics/risk-factors/     # Common risk factors
GET    /api/v1/mcq/analytics/completion-rates/ # Question completion rates
```

## Implementation Details

### 1. Serializers Required

#### QuestionCategorySerializer
```python
class QuestionCategorySerializer(serializers.ModelSerializer):
    question_count = serializers.IntegerField(read_only=True)
    completion_rate = serializers.FloatField(read_only=True)
    average_score = serializers.FloatField(read_only=True)
    
    class Meta:
        model = QuestionCategory
        fields = ['id', 'name', 'name_ko', 'description', 'weight', 
                  'order', 'question_count', 'completion_rate', 'average_score']
```

#### MultipleChoiceQuestionSerializer
```python
class MultipleChoiceQuestionSerializer(serializers.ModelSerializer):
    choices = QuestionChoiceSerializer(many=True, read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    depends_on_question = serializers.CharField(source='depends_on.question_text', read_only=True)
    
    class Meta:
        model = MultipleChoiceQuestion
        fields = ['id', 'category', 'category_name', 'question_text', 'question_text_ko',
                  'question_type', 'is_required', 'points', 'help_text', 'help_text_ko',
                  'depends_on', 'depends_on_question', 'depends_on_answer', 'order',
                  'choices', 'is_active']
```

#### QuestionResponseSerializer
```python
class QuestionResponseSerializer(serializers.ModelSerializer):
    question_text = serializers.CharField(source='question.question_text_ko', read_only=True)
    selected_choice_texts = serializers.StringRelatedField(
        source='selected_choices', many=True, read_only=True
    )
    
    class Meta:
        model = QuestionResponse
        fields = ['id', 'question', 'question_text', 'response_text',
                  'selected_choices', 'selected_choice_texts', 'points_earned']
        
    def validate(self, data):
        # Validate based on question type
        # Ensure required questions are answered
        # Check dependencies are satisfied
        return data
```

#### MCQAssessmentSerializer
```python
class MCQAssessmentSerializer(serializers.Serializer):
    knowledge_score = serializers.FloatField(read_only=True)
    lifestyle_score = serializers.FloatField(read_only=True)
    readiness_score = serializers.FloatField(read_only=True)
    comprehensive_score = serializers.FloatField(read_only=True)
    completion_status = serializers.DictField(read_only=True)
    risk_factors = serializers.ListField(read_only=True)
    insights = serializers.DictField(read_only=True)
    responses = QuestionResponseSerializer(many=True, read_only=True)
```

### 2. ViewSets and Views

#### QuestionCategoryViewSet
- List with pagination
- Filter by active status
- Include question counts
- Calculate completion rates

#### MultipleChoiceQuestionViewSet
- List with search functionality
- Filter by category, type, required
- Include dependency information
- Validate answer endpoint

#### MCQAssessmentAPIView
- Get current MCQ status
- Submit/update responses
- Calculate scores in real-time
- Return insights and recommendations

### 3. Permission Classes

```python
class MCQPermission(BasePermission):
    def has_permission(self, request, view):
        # Must be authenticated
        # Must be a trainer
        # Read-only for non-owners
        
    def has_object_permission(self, request, view, obj):
        # Must belong to same organization
        # Can only modify own assessments
```

### 4. Filters and Search

```python
class QuestionFilter(FilterSet):
    category = filters.CharFilter(field_name='category__slug')
    type = filters.ChoiceFilter(choices=QUESTION_TYPES)
    required = filters.BooleanFilter()
    search = filters.CharFilter(method='search_filter')
    
    def search_filter(self, queryset, name, value):
        return queryset.filter(
            Q(question_text__icontains=value) |
            Q(question_text_ko__icontains=value) |
            Q(help_text__icontains=value)
        )
```

### 5. Pagination

```python
class MCQPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
```

## API Documentation

### 1. OpenAPI/Swagger Integration
- Use drf-spectacular for auto-documentation
- Add detailed descriptions for each endpoint
- Include request/response examples
- Document error codes and messages

### 2. Example Requests

#### Get Questions by Category
```bash
GET /api/v1/mcq/categories/1/questions/
Authorization: Bearer {token}

Response:
{
  "count": 15,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "question_text_ko": "운동 지식 수준은?",
      "question_type": "single",
      "choices": [...]
    }
  ]
}
```

#### Submit MCQ Responses
```bash
POST /api/v1/assessments/123/mcq/responses/
Authorization: Bearer {token}
Content-Type: application/json

{
  "responses": [
    {
      "question_id": 1,
      "selected_choices": [2],
      "response_text": null
    },
    {
      "question_id": 5,
      "selected_choices": [],
      "response_text": "주 3회"
    }
  ]
}
```

### 3. Error Handling

Standard error response format:
```json
{
  "error": "validation_error",
  "message": "필수 질문에 답변하지 않았습니다.",
  "details": {
    "question_3": "이 질문은 필수입니다.",
    "question_7": "의존성이 충족되지 않았습니다."
  }
}
```

## Testing Requirements

### 1. Unit Tests
- Test all serializers with valid/invalid data
- Test permission classes
- Test filter logic
- Test pagination

### 2. Integration Tests
- Test complete MCQ submission flow
- Test dependency validation
- Test score calculations
- Test concurrent submissions

### 3. Performance Tests
- Test bulk operations
- Test query optimization
- Test caching effectiveness
- Test response times

## Security Considerations

1. **Authentication**: JWT tokens required for all endpoints
2. **Authorization**: Organization-based access control
3. **Rate Limiting**: Implement rate limits for submission endpoints
4. **Input Validation**: Strict validation on all inputs
5. **CORS**: Configure for mobile app domains only

## Performance Optimizations

1. **Prefetch Related**: Optimize queries with select_related/prefetch_related
2. **Caching**: Cache question data for 1 hour
3. **Bulk Operations**: Use bulk_create for batch submissions
4. **Database Indexes**: Add indexes on frequently queried fields

## Mobile App Considerations

1. **Offline Support**: Design API to support offline data collection
2. **Sync Mechanism**: Provide sync endpoints for offline data
3. **Compression**: Enable gzip compression for responses
4. **Versioning**: Use URL versioning (/api/v1/)

## Implementation Steps

1. **Create Serializers** (2 hours)
   - Implement all model serializers
   - Add validation logic
   - Create nested serializers

2. **Create ViewSets** (3 hours)
   - Implement CRUD operations
   - Add custom actions
   - Configure permissions

3. **Add Filters and Search** (1 hour)
   - Implement filter classes
   - Add search functionality
   - Configure ordering

4. **Create API Documentation** (1 hour)
   - Configure drf-spectacular
   - Add endpoint descriptions
   - Create example requests

5. **Write Tests** (2 hours)
   - Unit tests for serializers
   - Integration tests for views
   - Performance tests

6. **Performance Optimization** (1 hour)
   - Add select_related/prefetch_related
   - Implement caching
   - Optimize queries

## Success Criteria

1. All endpoints return correct data
2. Response times < 200ms for list operations
3. Response times < 100ms for detail operations
4. 100% test coverage for API code
5. Complete API documentation available
6. Mobile app successfully integrates

## Notes

- Ensure backward compatibility if API changes
- Consider GraphQL for future flexibility
- Monitor API usage for optimization opportunities
- Plan for API versioning strategy
- Consider webhook support for real-time updates