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
# Deploy refactored forms - using the new modular form structure
from .forms.refactored_forms import AssessmentWithTestsForm as AssessmentForm
from .forms import AssessmentSearchForm
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
    # Debug logging
    print(f"DEBUG - Assessment list view accessed by: {request.user}")
    print(f"DEBUG - Is superuser: {request.user.is_superuser}")
    print(f"DEBUG - Has trainer attr: {hasattr(request, 'trainer')}")
    print(f"DEBUG - Has organization attr: {hasattr(request, 'organization')}")
    
    form = AssessmentSearchForm(request.GET)
    
    # For superusers, show all assessments
    if request.user.is_superuser:
        assessments = Assessment.objects.all().select_related('client', 'trainer')
    else:
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
        
        # New filters
        gender = form.cleaned_data.get('gender')
        if gender:
            assessments = assessments.filter(client__gender=gender)
        
        age_min = form.cleaned_data.get('age_min')
        if age_min is not None:
            assessments = assessments.filter(client__age__gte=age_min)
        
        age_max = form.cleaned_data.get('age_max')
        if age_max is not None:
            assessments = assessments.filter(client__age__lte=age_max)
        
        bmi_range = form.cleaned_data.get('bmi_range')
        if bmi_range:
            # Use Django's annotate for BMI calculation
            from django.db.models import F, FloatField, ExpressionWrapper
            assessments_with_bmi = assessments.annotate(
                bmi=ExpressionWrapper(
                    F('client__weight') / (F('client__height') * F('client__height') / 10000),
                    output_field=FloatField()
                )
            )
            
            if bmi_range == 'underweight':
                # BMI < 18.5
                assessments = assessments_with_bmi.filter(bmi__lt=18.5)
            elif bmi_range == 'normal':
                # BMI 18.5-24.9
                assessments = assessments_with_bmi.filter(bmi__gte=18.5, bmi__lt=25)
            elif bmi_range == 'overweight':
                # BMI 25-29.9
                assessments = assessments_with_bmi.filter(bmi__gte=25, bmi__lt=30)
            elif bmi_range == 'obese':
                # BMI >= 30
                assessments = assessments_with_bmi.filter(bmi__gte=30)
        
        risk_range = form.cleaned_data.get('risk_range')
        if risk_range:
            if risk_range == '0-20':
                assessments = assessments.filter(injury_risk_score__lte=20)
            elif risk_range == '21-40':
                assessments = assessments.filter(injury_risk_score__gt=20, injury_risk_score__lte=40)
            elif risk_range == '41-60':
                assessments = assessments.filter(injury_risk_score__gt=40, injury_risk_score__lte=60)
            elif risk_range == '61-80':
                assessments = assessments.filter(injury_risk_score__gt=60, injury_risk_score__lte=80)
            elif risk_range == '81-100':
                assessments = assessments.filter(injury_risk_score__gt=80)
        
        strength_range = form.cleaned_data.get('strength_range')
        if strength_range:
            if strength_range == '80-100':
                assessments = assessments.filter(strength_score__gte=80)
            elif strength_range == '60-79':
                assessments = assessments.filter(strength_score__gte=60, strength_score__lt=80)
            elif strength_range == '40-59':
                assessments = assessments.filter(strength_score__gte=40, strength_score__lt=60)
            elif strength_range == '0-39':
                assessments = assessments.filter(strength_score__lt=40)
        
        mobility_range = form.cleaned_data.get('mobility_range')
        if mobility_range:
            if mobility_range == '80-100':
                assessments = assessments.filter(mobility_score__gte=80)
            elif mobility_range == '60-79':
                assessments = assessments.filter(mobility_score__gte=60, mobility_score__lt=80)
            elif mobility_range == '40-59':
                assessments = assessments.filter(mobility_score__gte=40, mobility_score__lt=60)
            elif mobility_range == '0-39':
                assessments = assessments.filter(mobility_score__lt=40)
    
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
    # For superusers, allow viewing any assessment
    if request.user.is_superuser:
        assessment = get_object_or_404(
            Assessment.objects.select_related('client', 'trainer'),
            pk=pk
        )
    else:
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
        # HTMX request - return content only
        return render(request, 'assessments/assessment_detail_content.html', context)
    else:
        # Regular request - return full page with base template
        return render(request, 'assessments/assessment_detail.html', context)


@login_required
@requires_trainer
@organization_member_required
def assessment_add_view(request):
    """Add new assessment with multi-step form"""
    client_id = request.GET.get('client')
    client = None
    
    if client_id:
        # For superusers, allow accessing any client
        if request.user.is_superuser:
            client = get_object_or_404(Client, pk=client_id)
        else:
            # Ensure client belongs to the same organization
            client = get_object_or_404(
                Client, 
                pk=client_id, 
                trainer__organization=request.organization
            )
    
    if request.method == 'POST':
        form = AssessmentForm(data=request.POST, user=request.user)
        if form.is_valid():
            try:
                # The refactored form handles all saving logic including:
                # - Trainer assignment
                # - Score calculation
                # - Date conversion
                assessment = form.save(commit=True)
                
                # Additional trainer assignment for superusers if needed
                if assessment and request.user.is_superuser and not hasattr(request, 'trainer'):
                    if not assessment.trainer and assessment.client:
                        assessment.trainer = assessment.client.trainer
                        assessment.save()
            except Exception as e:
                messages.error(request, f'평가 저장 중 오류가 발생했습니다: {str(e)}')
                return redirect('assessments:add')
            
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
        # Create a temporary assessment instance with initial values
        temp_assessment = Assessment(date=timezone.now().date())
        if client:
            temp_assessment.client = client
        form = AssessmentForm(instance=temp_assessment, user=request.user)
    
    context = {
        'form': form,
        'client': client,
        'clients': Client.objects.all() if request.user.is_superuser and not client 
                   else Client.objects.filter(
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
    # For superusers, allow deleting any assessment
    if request.user.is_superuser:
        assessment = get_object_or_404(Assessment, pk=pk)
    else:
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
    
    # Debug mode - use simpler template if debug parameter is present
    if request.GET.get('debug'):
        return mcq_assessment_debug_view(request, assessment_id)
    
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
        'existing_responses': json.dumps(response_data) if response_data else '{}'
    }
    
    # Temporarily use simple template to avoid Alpine.js issues
    return render(request, 'assessments/mcq_assessment_simple.html', context)


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
    
    try:
        # Get all questions
        questions = MultipleChoiceQuestion.objects.filter(
            is_active=True,
            category__is_active=True
        ).prefetch_related('choices')
        
        # Process each question
        for question in questions:
            field_name = f'question_{question.id}'
            
            if field_name in request.POST:
                # Get or create response (update existing instead of delete/create)
                response, created = QuestionResponse.objects.get_or_create(
                    assessment=assessment,
                    question=question,
                    defaults={'points_earned': 0}
                )
                
                # Clear existing choices before adding new ones
                response.selected_choices.clear()
                
                if question.question_type == 'text':
                    response.response_text = request.POST.get(field_name, '')
                    response.save()
                elif question.question_type == 'multiple':
                    # Handle multiple checkboxes
                    choice_ids = request.POST.getlist(field_name)
                    for choice_id in choice_ids:
                        try:
                            choice = question.choices.get(id=choice_id)
                            response.selected_choices.add(choice)
                        except QuestionChoice.DoesNotExist:
                            pass
                else:
                    # Single choice or scale
                    choice_id = request.POST.get(field_name)
                    if choice_id:
                        try:
                            if question.question_type == 'scale':
                                # For scale, save as text
                                response.response_text = choice_id
                                response.save()
                            else:
                                choice = question.choices.get(id=choice_id)
                                response.selected_choices.add(choice)
                        except (QuestionChoice.DoesNotExist, ValueError):
                            pass
        
        # Debug: Check if responses exist
        response_count = assessment.question_responses.count()
        print(f"DEBUG - Total responses saved: {response_count}")
        
        # Calculate MCQ scores
        assessment.calculate_scores()
        assessment.save()  # Save the calculated MCQ scores to database
        
        # Debug: Check if scores were actually saved
        assessment.refresh_from_db()
        print(f"DEBUG - After save: knowledge_score={assessment.knowledge_score}, "
              f"lifestyle_score={assessment.lifestyle_score}, "
              f"readiness_score={assessment.readiness_score}, "
              f"comprehensive_score={assessment.comprehensive_score}")
        
        messages.success(request, 'MCQ 평가가 성공적으로 저장되었습니다.')
        
        # Return result view for HTMX
        if request.headers.get('HX-Request'):
            return mcq_result_partial(request, assessment)
        
        return redirect('assessments:detail', pk=assessment.pk)
        
    except Exception as e:
        messages.error(request, f'평가 저장 중 오류가 발생했습니다: {str(e)}')
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
def mcq_assessment_debug_view(request, assessment_id):
    """Debug view for MCQ assessment"""
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
    ).select_related('category').order_by('category__order', 'order')
    
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
        'existing_responses': json.dumps(response_data) if response_data else '{}'
    }
    
    return render(request, 'assessments/mcq_assessment_debug.html', context)


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


@login_required
@requires_trainer
@organization_member_required
def assessment_compare_view(request):
    """Compare multiple assessments side by side"""
    if request.method == 'POST':
        # Get selected assessment IDs
        assessment_ids = request.POST.getlist('assessment_ids')
        
        # Validate we have 2-5 assessments
        if len(assessment_ids) < 2 or len(assessment_ids) > 5:
            messages.error(request, '비교를 위해 2-5개의 평가를 선택해주세요.')
            return redirect('assessments:list')
        
        # Fetch assessments
        if request.user.is_superuser:
            assessments = Assessment.objects.filter(
                id__in=assessment_ids
            ).select_related('client', 'trainer').order_by('-date')
        else:
            assessments = Assessment.objects.filter(
                id__in=assessment_ids,
                trainer__organization=request.organization
            ).select_related('client', 'trainer').order_by('-date')
        
        # Ensure we got all requested assessments
        if assessments.count() != len(assessment_ids):
            messages.error(request, '일부 평가를 찾을 수 없습니다.')
            return redirect('assessments:list')
        
        # Prepare comparison data
        comparison_data = []
        for assessment in assessments:
            data = {
                'assessment': assessment,
                'client': assessment.client,
                'scores': {
                    'overall': assessment.overall_score or 0,
                    'strength': assessment.strength_score or 0,
                    'mobility': assessment.mobility_score or 0,
                    'balance': assessment.balance_score or 0,
                    'cardio': assessment.cardio_score or 0
                },
                'tests': {
                    'overhead_squat': assessment.overhead_squat_score,
                    'push_up': assessment.push_up_reps,
                    'balance_avg': None,
                    'toe_touch': assessment.toe_touch_distance,
                    'shoulder_mobility': assessment.shoulder_mobility_score,
                    'farmer_carry': assessment.farmer_carry_score,
                    'risk': assessment.injury_risk_score
                }
            }
            
            # Calculate average balance score
            balance_values = [
                assessment.single_leg_balance_right_eyes_open,
                assessment.single_leg_balance_left_eyes_open,
                assessment.single_leg_balance_right_eyes_closed,
                assessment.single_leg_balance_left_eyes_closed
            ]
            balance_values = [v for v in balance_values if v is not None]
            if balance_values:
                data['tests']['balance_avg'] = sum(balance_values) / len(balance_values)
            
            comparison_data.append(data)
        
        # Calculate averages and find best performers
        score_categories = ['overall', 'strength', 'mobility', 'balance', 'cardio']
        best_performers = {}
        
        for category in score_categories:
            scores = [(i, data['scores'][category]) for i, data in enumerate(comparison_data)]
            if scores:
                best_idx = max(scores, key=lambda x: x[1])[0]
                best_performers[category] = best_idx
        
        context = {
            'comparison_data': comparison_data,
            'best_performers': best_performers,
            'score_categories': score_categories
        }
        
        # Check if this is an HTMX request
        if request.headers.get('HX-Request'):
            return render(request, 'assessments/assessment_compare_content.html', context)
        else:
            return render(request, 'assessments/assessment_compare.html', context)
    
    # GET request - redirect to list
    return redirect('assessments:list')


@login_required
def timer_test_view(request):
    """Timer test page for demonstration."""
    if request.headers.get('HX-Request'):
        return render(request, 'assessments/timer_test_content.html')
    return render(request, 'assessments/timer_test.html')


@login_required
def timer_debug_view(request):
    """Timer debug page."""
    return render(request, 'assessments/timer_debug.html')


@login_required  
def timer_inline_test_view(request):
    """Timer inline test page."""
    return render(request, 'assessments/timer_inline_test.html')
