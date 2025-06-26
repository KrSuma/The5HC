"""
Optimized views for assessments using the refactored model structure.
These views demonstrate efficient query patterns with the new OneToOneField relationships.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Prefetch
from django.core.paginator import Paginator

from .models import Assessment
from .forms import AssessmentSearchForm
from apps.trainers.decorators import requires_trainer, organization_member_required


@login_required
@requires_trainer
@organization_member_required
def assessment_list_optimized_view(request):
    """
    Optimized list view that efficiently loads all test relationships.
    
    Key optimizations:
    1. Uses select_related for all OneToOneField relationships
    2. Single query to fetch all related test data
    3. No N+1 queries when accessing test scores in templates
    """
    form = AssessmentSearchForm(request.GET)
    
    # Start with optimized queryset
    if request.user.is_superuser:
        # Use the custom manager method for optimized queries
        assessments = Assessment.objects.with_all_tests()
    else:
        # Filter by organization and include all test data
        assessments = Assessment.objects.with_all_tests().filter(
            trainer__organization=request.organization
        )
    
    # Apply search filters
    if form.is_valid():
        search = form.cleaned_data.get('search')
        if search:
            assessments = assessments.filter(
                Q(client__name__icontains=search) |
                Q(client__email__icontains=search)
            )
        
        # Apply other filters...
        score_range = form.cleaned_data.get('score_range')
        if score_range:
            if score_range == '90-100':
                assessments = assessments.filter(overall_score__gte=90)
            elif score_range == '80-89':
                assessments = assessments.filter(overall_score__gte=80, overall_score__lt=90)
            # ... etc
    
    # Order and paginate
    assessments = assessments.order_by('-date')
    paginator = Paginator(assessments, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'assessments': page_obj,
        'form': form,
        'total_count': paginator.count
    }
    
    # Use optimized template
    if request.headers.get('HX-Request'):
        return render(request, 'assessments/assessment_list_optimized_content.html', context)
    else:
        return render(request, 'assessments/assessment_list_optimized.html', context)


@login_required
@requires_trainer
@organization_member_required
def assessment_detail_optimized_view(request, pk):
    """
    Optimized detail view that loads all test data in a single query.
    
    Key optimizations:
    1. Single query with all related test models
    2. No additional queries when accessing test fields
    3. Efficient score calculations using model methods
    """
    if request.user.is_superuser:
        # Superusers can view any assessment
        assessment = get_object_or_404(
            Assessment.objects.with_all_tests(),
            pk=pk
        )
    else:
        # Regular trainers only see their organization's assessments
        assessment = get_object_or_404(
            Assessment.objects.with_all_tests(),
            pk=pk,
            trainer__organization=request.organization
        )
    
    # Calculate all test scores efficiently
    test_scores = {
        'overhead_squat': assessment.overhead_squat_test.calculate_score() if hasattr(assessment, 'overhead_squat_test') else None,
        'push_up': assessment.push_up_test.calculate_score() if hasattr(assessment, 'push_up_test') else None,
        'balance': assessment.single_leg_balance_test.calculate_score() if hasattr(assessment, 'single_leg_balance_test') else None,
        'toe_touch': assessment.toe_touch_test.calculate_score() if hasattr(assessment, 'toe_touch_test') else None,
        'shoulder_mobility': assessment.shoulder_mobility_test.calculate_score() if hasattr(assessment, 'shoulder_mobility_test') else None,
        'farmers_carry': assessment.farmers_carry_test.calculate_score() if hasattr(assessment, 'farmers_carry_test') else None,
        'harvard_step': assessment.harvard_step_test.calculate_score() if hasattr(assessment, 'harvard_step_test') else None,
    }
    
    # Get percentile rankings and other data
    percentile_rankings = assessment.get_percentile_rankings()
    performance_age_data = assessment.calculate_performance_age()
    
    # Calculate score descriptions
    from .scoring import get_score_description
    score_descriptions = {
        'overall': get_score_description(assessment.overall_score or 0),
        'strength': get_score_description(assessment.strength_score or 0, 50),
        'mobility': get_score_description(assessment.mobility_score or 0, 50),
        'balance': get_score_description(assessment.balance_score or 0, 50),
        'cardio': get_score_description(assessment.cardio_score or 0, 40)
    }
    
    context = {
        'assessment': assessment,
        'test_scores': test_scores,
        'score_descriptions': score_descriptions,
        'percentile_rankings': percentile_rankings,
        'performance_age': performance_age_data,
    }
    
    # Use optimized template
    if request.headers.get('HX-Request'):
        return render(request, 'assessments/assessment_detail_optimized_content.html', context)
    else:
        return render(request, 'assessments/assessment_detail_optimized.html', context)


@login_required
@requires_trainer
@organization_member_required
def assessment_comparison_optimized_view(request):
    """
    Optimized comparison view for multiple assessments.
    
    Efficiently loads multiple assessments with all test data
    for side-by-side comparison.
    """
    assessment_ids = request.GET.getlist('id')
    
    if not assessment_ids or len(assessment_ids) < 2:
        messages.error(request, "비교를 위해 최소 2개의 평가를 선택해주세요.")
        return redirect('assessments:list')
    
    # Limit to 5 assessments
    assessment_ids = assessment_ids[:5]
    
    # Load all assessments with optimized query
    if request.user.is_superuser:
        assessments = Assessment.objects.with_all_tests().filter(
            pk__in=assessment_ids
        ).order_by('-date')
    else:
        assessments = Assessment.objects.with_all_tests().filter(
            pk__in=assessment_ids,
            trainer__organization=request.organization
        ).order_by('-date')
    
    # Prepare comparison data
    comparison_data = []
    for assessment in assessments:
        data = {
            'assessment': assessment,
            'scores': {
                'overhead_squat': assessment.overhead_squat_test.calculate_score() if hasattr(assessment, 'overhead_squat_test') else None,
                'push_up': assessment.push_up_test.calculate_score() if hasattr(assessment, 'push_up_test') else None,
                'balance': assessment.single_leg_balance_test.calculate_score() if hasattr(assessment, 'single_leg_balance_test') else None,
                'toe_touch': assessment.toe_touch_test.calculate_score() if hasattr(assessment, 'toe_touch_test') else None,
                'shoulder_mobility': assessment.shoulder_mobility_test.calculate_score() if hasattr(assessment, 'shoulder_mobility_test') else None,
                'farmers_carry': assessment.farmers_carry_test.calculate_score() if hasattr(assessment, 'farmers_carry_test') else None,
                'harvard_step': assessment.harvard_step_test.calculate_score() if hasattr(assessment, 'harvard_step_test') else None,
            }
        }
        comparison_data.append(data)
    
    context = {
        'comparison_data': comparison_data,
        'assessment_count': len(assessments)
    }
    
    if request.headers.get('HX-Request'):
        return render(request, 'assessments/assessment_comparison_optimized_content.html', context)
    else:
        return render(request, 'assessments/assessment_comparison_optimized.html', context)