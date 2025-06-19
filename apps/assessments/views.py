from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.db.models import Q, Avg, Count
from django.core.paginator import Paginator
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.template.loader import render_to_string
import json

from .models import Assessment, QuestionCategory, MultipleChoiceQuestion, QuestionResponse
from .forms import AssessmentForm, AssessmentSearchForm
from .forms.mcq_forms import MCQResponseForm, CategoryMCQFormSet
from apps.clients.models import Client
from apps.trainers.decorators import requires_trainer, organization_member_required

# Import scoring functions from the Django app
from .scoring import (
    calculate_pushup_score, calculate_single_leg_balance_score,
    calculate_toe_touch_score, calculate_farmers_carry_score,
    calculate_step_test_score, calculate_category_scores, 
    get_score_description
)

# Check if WeasyPrint is available
try:
    from apps.reports.services import WEASYPRINT_AVAILABLE
except ImportError:
    WEASYPRINT_AVAILABLE = False


@login_required
@requires_trainer
@organization_member_required
def assessment_list_view(request):
    """List all assessments with search and filter functionality"""
    form = AssessmentSearchForm(request.GET)
    # Filter assessments by organization
    assessments = Assessment.objects.filter(
        trainer__organization=request.organization
    ).select_related('client', 'trainer')
    
    # Apply filters
    if form.is_valid():
        search = form.cleaned_data.get('search')
        if search:
            assessments = assessments.filter(
                Q(client__name__icontains=search) |
                Q(client__email__icontains=search)
            )
        
        date_from = form.cleaned_data.get('date_from')
        if date_from:
            assessments = assessments.filter(date__date__gte=date_from)
            
        date_to = form.cleaned_data.get('date_to')
        if date_to:
            assessments = assessments.filter(date__date__lte=date_to)
            
        score_range = form.cleaned_data.get('score_range')
        if score_range:
            if score_range == '90-100':
                assessments = assessments.filter(overall_score__gte=90)
            elif score_range == '80-89':
                assessments = assessments.filter(overall_score__gte=80, overall_score__lt=90)
            elif score_range == '70-79':
                assessments = assessments.filter(overall_score__gte=70, overall_score__lt=80)
            elif score_range == '60-69':
                assessments = assessments.filter(overall_score__gte=60, overall_score__lt=70)
            elif score_range == '0-59':
                assessments = assessments.filter(overall_score__lt=60)
    
    # Pagination
    paginator = Paginator(assessments, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistics
    stats = assessments.aggregate(
        total_count=Count('id'),
        avg_score=Avg('overall_score')
    )
    
    context = {
        'form': form,
        'page_obj': page_obj,
        'stats': stats
    }
    
    # HTMX handling - return full content for navigation, partial for pagination/search
    if request.headers.get('HX-Request'):
        # Check if this is a navigation request or just pagination/search
        if request.headers.get('HX-Target') == 'main-content':
            # Navigation request - return content without base.html
            return render(request, 'assessments/assessment_list_content.html', context)
        else:
            # Pagination/search - return only the table
            html = render_to_string(
                'assessments/assessment_list_partial.html',
                {'page_obj': page_obj, 'request': request}
            )
            return HttpResponse(html)
    
    return render(request, 'assessments/assessment_list.html', context)


@login_required
@requires_trainer
@organization_member_required
def assessment_detail_view(request, pk):
    """View detailed assessment results"""
    # Ensure assessment belongs to the same organization
    assessment = get_object_or_404(
        Assessment.objects.select_related('client', 'trainer'),
        pk=pk,
        trainer__organization=request.organization
    )
    
    # Get score descriptions
    score_descriptions = {
        'overall': get_score_description(assessment.overall_score or 0),
        'strength': get_score_description(assessment.strength_score or 0, 50),
        'mobility': get_score_description(assessment.mobility_score or 0, 50),
        'balance': get_score_description(assessment.balance_score or 0, 50),
        'cardio': get_score_description(assessment.cardio_score or 0, 40)
    }
    
    # Get percentile rankings
    percentile_rankings = assessment.get_percentile_rankings()
    
    # Get performance age
    performance_age_data = assessment.calculate_performance_age()
    
    # Translate primary concerns to Korean if available
    if assessment.risk_factors and 'summary' in assessment.risk_factors:
        from apps.assessments.risk_calculator_korean import get_korean_primary_concerns
        assessment.risk_factors['summary']['primary_concerns'] = get_korean_primary_concerns(assessment.risk_factors)
    
    context = {
        'assessment': assessment,
        'score_descriptions': score_descriptions,
        'percentile_rankings': percentile_rankings,
        'performance_age': performance_age_data,
        'weasyprint_available': WEASYPRINT_AVAILABLE
    }
    
    # Check if this is an HTMX request
    if request.headers.get('HX-Request'):
        # Create a partial template for HTMX requests
        return render(request, 'assessments/assessment_detail_partial.html', context)
    
    return render(request, 'assessments/assessment_detail.html', context)


@login_required
@requires_trainer
@organization_member_required
def assessment_add_view(request):
    """Add new assessment with multi-step form"""
    client_id = request.GET.get('client')
    client = None
    
    if client_id:
        # Ensure client belongs to the same organization
        client = get_object_or_404(
            Client, 
            pk=client_id, 
            trainer__organization=request.organization
        )
    
    if request.method == 'POST':
        form = AssessmentForm(request.POST)
        if form.is_valid():
            assessment = form.save(commit=False)
            assessment.trainer = request.trainer
            
            # Convert date to datetime if needed
            if assessment.date and not hasattr(assessment.date, 'hour'):
                from datetime import datetime, time
                assessment.date = datetime.combine(assessment.date, time.min)
            
            # Calculate scores before saving
            assessment_data = {
                'push_up_score': form.cleaned_data.get('push_up_score'),
                'farmers_carry_score': form.cleaned_data.get('farmer_carry_score'),
                'toe_touch_score': form.cleaned_data.get('toe_touch_score'),
                'shoulder_mobility_score': form.cleaned_data.get('shoulder_mobility_score'),
                'overhead_squat_score': form.cleaned_data.get('overhead_squat_score'),
                'single_leg_balance_right_open': form.cleaned_data.get('single_leg_balance_right_eyes_open'),
                'single_leg_balance_left_open': form.cleaned_data.get('single_leg_balance_left_eyes_open'),
                'single_leg_balance_right_closed': form.cleaned_data.get('single_leg_balance_right_eyes_closed'),
                'single_leg_balance_left_closed': form.cleaned_data.get('single_leg_balance_left_eyes_closed'),
                'step_test_hr1': form.cleaned_data.get('harvard_step_test_hr1', 90),
                'step_test_hr2': form.cleaned_data.get('harvard_step_test_hr2', 80),
                'step_test_hr3': form.cleaned_data.get('harvard_step_test_hr3', 70)
            }
            
            client_details = {
                'gender': assessment.client.gender,
                'age': assessment.client.age
            }
            
            scores = calculate_category_scores(assessment_data, client_details)
            assessment.overall_score = scores['overall_score']
            assessment.strength_score = scores['strength_score']
            assessment.mobility_score = scores['mobility_score']
            assessment.balance_score = scores['balance_score']
            assessment.cardio_score = scores['cardio_score']
            
            assessment.save()
            
            messages.success(request, '평가가 성공적으로 저장되었습니다.')
            
            if request.headers.get('HX-Request'):
                return HttpResponse(
                    status=204,
                    headers={'HX-Redirect': f'/assessments/{assessment.pk}/'}
                )
            return redirect('assessments:detail', pk=assessment.pk)
        else:
            if request.headers.get('HX-Request'):
                html = render_to_string(
                    'assessments/assessment_form_partial.html',
                    {'form': form, 'client': client, 'request': request}
                )
                return HttpResponse(html)
    else:
        initial = {'date': timezone.now().date()}
        if client:
            initial['client'] = client.pk
        form = AssessmentForm(initial=initial)
    
    context = {
        'form': form,
        'client': client,
        'clients': Client.objects.filter(
            trainer__organization=request.organization
        ) if not client else None
    }
    
    # Check for HTMX navigation request
    if request.headers.get('HX-Request') and request.headers.get('HX-Target') == 'main-content':
        return render(request, 'assessments/assessment_form_content.html', context)
    
    return render(request, 'assessments/assessment_form.html', context)


@login_required
@requires_trainer
@require_http_methods(["GET"])
def calculate_push_up_score_ajax(request):
    """AJAX endpoint to calculate push-up score"""
    try:
        gender = request.GET.get('gender')
        age = int(request.GET.get('age', 0))
        reps = int(request.GET.get('reps', 0))
        
        score = calculate_pushup_score(gender, age, reps)
        
        return JsonResponse({'score': score})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
@requires_trainer
@require_http_methods(["GET"])
def calculate_balance_score_ajax(request):
    """AJAX endpoint to calculate balance score"""
    try:
        right_open = int(request.GET.get('right_open', 0))
        left_open = int(request.GET.get('left_open', 0))
        right_closed = int(request.GET.get('right_closed', 0))
        left_closed = int(request.GET.get('left_closed', 0))
        
        score = calculate_single_leg_balance_score(
            right_open, left_open, right_closed, left_closed
        )
        
        return JsonResponse({'score': int(round(score))})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
@requires_trainer
@require_http_methods(["GET"])
def calculate_toe_touch_score_ajax(request):
    """AJAX endpoint to calculate toe touch score"""
    try:
        distance = float(request.GET.get('distance', 0))
        score = calculate_toe_touch_score(distance)
        
        return JsonResponse({'score': score})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
@requires_trainer
@require_http_methods(["GET"])
def calculate_farmer_score_ajax(request):
    """AJAX endpoint to calculate farmer's carry score"""
    try:
        gender = request.GET.get('gender')
        weight = float(request.GET.get('weight', 0))
        distance = float(request.GET.get('distance', 0))
        time = int(request.GET.get('time', 60))  # Default 60 seconds
        
        score = calculate_farmers_carry_score(gender, weight, distance, time)
        
        return JsonResponse({'score': int(round(score))})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


def calculate_harvard_score_ajax(request):
    """AJAX endpoint to calculate Harvard Step Test score"""
    try:
        hr1 = int(request.GET.get('hr1', 0))
        hr2 = int(request.GET.get('hr2', 0))
        hr3 = int(request.GET.get('hr3', 0))
        
        score, pfi = calculate_step_test_score(hr1, hr2, hr3)
        
        return JsonResponse({
            'score': score,
            'pfi': round(pfi, 2)
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
@requires_trainer
@organization_member_required
def assessment_delete_view(request, pk):
    """Delete assessment"""
    # Ensure assessment belongs to the same organization
    assessment = get_object_or_404(
        Assessment, 
        pk=pk, 
        trainer__organization=request.organization
    )
    
    if request.method == 'POST':
        assessment.delete()
        messages.success(request, '평가가 삭제되었습니다.')
        
        if request.headers.get('HX-Request'):
            return HttpResponse(status=204, headers={'HX-Redirect': '/assessments/'})
        return redirect('assessments:list')
    
    return render(request, 'assessments/assessment_confirm_delete.html', {
        'assessment': assessment
    })


@login_required
@requires_trainer
@organization_member_required
def mcq_assessment_view(request, assessment_id):
    """Display MCQ assessment form with progressive disclosure"""
    assessment = get_object_or_404(
        Assessment,
        pk=assessment_id,
        trainer__organization=request.organization
    )
    
    # Get active categories
    categories = QuestionCategory.objects.filter(
        is_active=True
    ).order_by('order')
    
    # Get all active questions
    questions = MultipleChoiceQuestion.objects.filter(
        is_active=True,
        category__in=categories
    ).select_related('category', 'depends_on').prefetch_related('choices').order_by('category__order', 'order')
    
    # Get existing responses
    existing_responses = QuestionResponse.objects.filter(
        assessment=assessment
    ).select_related('question').prefetch_related('selected_choices')
    
    # Build response data for form initialization
    response_data = {}
    for response in existing_responses:
        field_name = f'question_{response.question.id}'
        if response.question.question_type == 'text':
            response_data[field_name] = response.response_text
        elif response.question.question_type == 'multiple':
            response_data[field_name] = list(response.selected_choices.values_list('id', flat=True))
        else:
            choice = response.selected_choices.first()
            if choice:
                response_data[field_name] = choice.id
    
    context = {
        'assessment': assessment,
        'client': assessment.client,
        'categories': categories,
        'questions': questions,
        'existing_responses': response_data
    }
    
    return render(request, 'assessments/mcq_assessment.html', context)


@login_required
@requires_trainer
@organization_member_required
@require_http_methods(["POST"])
def mcq_save_view(request, assessment_id):
    """Save MCQ responses and calculate scores"""
    assessment = get_object_or_404(
        Assessment,
        pk=assessment_id,
        trainer__organization=request.organization
    )
    
    # Get categories for form processing
    categories = QuestionCategory.objects.filter(is_active=True)
    
    # Create formset with POST data
    formset = CategoryMCQFormSet(
        data=request.POST,
        assessment=assessment,
        categories=categories
    )
    
    if formset.is_valid():
        # Save all responses
        formset.save()
        
        # Calculate MCQ scores
        assessment.calculate_scores()
        
        messages.success(request, 'MCQ 평가가 성공적으로 저장되었습니다.')
        
        # Return result view for HTMX
        if request.headers.get('HX-Request'):
            return mcq_result_partial(request, assessment)
        
        return redirect('assessments:detail', pk=assessment.pk)
    else:
        # Return form with errors
        if request.headers.get('HX-Request'):
            context = {
                'assessment': assessment,
                'formset': formset,
                'categories': categories
            }
            html = render_to_string(
                'assessments/components/mcq_form_errors.html',
                context,
                request=request
            )
            return HttpResponse(html)
        
        messages.error(request, '평가 저장 중 오류가 발생했습니다.')
        return redirect('assessments:mcq', assessment_id=assessment.pk)


def mcq_result_partial(request, assessment):
    """Render MCQ result partial for HTMX response"""
    # Get MCQ insights
    insights = assessment.get_mcq_insights()
    
    # Get completion status
    completion_status = assessment.get_mcq_completion_status()
    
    context = {
        'assessment': assessment,
        'insights': insights,
        'completion_status': completion_status,
        'knowledge_score': assessment.knowledge_score,
        'lifestyle_score': assessment.lifestyle_score,
        'readiness_score': assessment.readiness_score,
        'comprehensive_score': assessment.comprehensive_score
    }
    
    html = render_to_string(
        'assessments/components/mcq_result.html',
        context,
        request=request
    )
    
    return HttpResponse(html)


@login_required
@requires_trainer
@organization_member_required
def mcq_quick_form_view(request, assessment_id):
    """Quick MCQ entry form for basic questions during assessment"""
    assessment = get_object_or_404(
        Assessment,
        pk=assessment_id,
        trainer__organization=request.organization
    )
    
    if request.method == 'POST':
        # Process quick form
        # This would map the simplified form to actual MCQ questions
        # For now, we'll just redirect back
        messages.info(request, 'Quick MCQ 저장 기능은 준비 중입니다.')
        return redirect('assessments:detail', pk=assessment.pk)
    
    context = {
        'assessment': assessment,
        'client': assessment.client
    }
    
    return render(request, 'assessments/mcq_quick_form.html', context)


@login_required
@requires_trainer
@organization_member_required
def mcq_print_view(request, assessment_id):
    """Print-friendly view of MCQ assessment with all questions and responses"""
    assessment = get_object_or_404(
        Assessment,
        pk=assessment_id,
        trainer__organization=request.organization
    )
    
    # Get all categories with questions
    categories = QuestionCategory.objects.filter(
        is_active=True
    ).prefetch_related(
        'multiplechoicequestion_set__choices',
        'multiplechoicequestion_set__questionresponse_set__selected_choices'
    ).order_by('order')
    
    # Get all responses for this assessment
    responses = {}
    for response in QuestionResponse.objects.filter(assessment=assessment).select_related('question'):
        responses[response.question.id] = response
    
    # Get MCQ insights and risk factors
    insights = assessment.get_mcq_insights()
    mcq_scoring = assessment.get_mcq_risk_factors()
    
    context = {
        'assessment': assessment,
        'categories': categories,
        'responses': responses,
        'category_insights': insights,
        'mcq_risk_factors': mcq_scoring.get('risk_factors', []) if mcq_scoring else []
    }
    
    # Create a custom template tag filter to get items from dict
    from django import template
    register = template.Library()
    
    @register.filter
    def get_item(dictionary, key):
        return dictionary.get(key)
    
    # Note: In production, this filter should be in a templatetags file
    
    return render(request, 'assessments/mcq_print.html', context)
