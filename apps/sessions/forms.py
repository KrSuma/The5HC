from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
from .models import SessionPackage, Session, Payment
from apps.clients.models import Client


class SessionPackageForm(forms.ModelForm):
    """Form for creating and editing session packages"""
    
    class Meta:
        model = SessionPackage
        fields = [
            'client', 'package_name', 'total_amount', 'session_price', 
            'total_sessions', 'notes', 'is_active'
        ]
        
        widgets = {
            'client': forms.Select(
                attrs={
                    'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                    'x-model': 'selectedClient',
                    '@change': 'clientChanged()'
                }
            ),
            'package_name': forms.TextInput(
                attrs={
                    'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                    'placeholder': '예: 10회 퍼스널 트레이닝'
                }
            ),
            'total_amount': forms.NumberInput(
                attrs={
                    'class': 'w-full pl-8 pr-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                    'placeholder': '원',
                    'step': '1000',
                    'min': '0',
                    'x-model': 'totalAmount',
                    '@input': 'calculateFees()'
                }
            ),
            'session_price': forms.NumberInput(
                attrs={
                    'class': 'w-full pl-8 pr-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                    'placeholder': '원',
                    'step': '1000',
                    'min': '0',
                    'x-model': 'sessionPrice',
                    '@input': 'onSessionPriceChange()'
                }
            ),
            'total_sessions': forms.NumberInput(
                attrs={
                    'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                    'min': '1',
                    'x-model': 'totalSessions',
                    '@input': 'onTotalSessionsChange()'
                }
            ),
            'vat_rate': forms.NumberInput(
                attrs={
                    'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                    'step': '0.01',
                    'min': '0',
                    'max': '1',
                    'x-model': 'vatRate',
                    '@input': 'calculateFees()'
                }
            ),
            'card_fee_rate': forms.NumberInput(
                attrs={
                    'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                    'step': '0.01',
                    'min': '0',
                    'max': '1',
                    'x-model': 'cardFeeRate',
                    '@input': 'calculateFees()'
                }
            ),
            'fee_calculation_method': forms.Select(
                attrs={
                    'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                    'x-model': 'feeMethod',
                    '@change': 'calculateFees()'
                }
            ),
            'notes': forms.Textarea(
                attrs={
                    'rows': 3,
                    'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                    'placeholder': '패키지 관련 메모 (선택사항)'
                }
            ),
            'is_active': forms.CheckboxInput(
                attrs={
                    'class': 'h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded'
                }
            ),
        }
        
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user:
            self.fields['client'].queryset = Client.objects.filter(trainer=user)
        
        # No need to set default values for vat_rate, card_fee_rate, fee_calculation_method
        # as they are now set programmatically in the view
        
        # If editing existing package, calculate remaining values
        if self.instance.pk:
            self.fields['total_sessions'].widget.attrs['readonly'] = True
            self.fields['session_price'].widget.attrs['readonly'] = True
            
    def clean(self):
        cleaned_data = super().clean()
        total_amount = cleaned_data.get('total_amount')
        session_price = cleaned_data.get('session_price')
        total_sessions = cleaned_data.get('total_sessions')
        
        if total_amount and session_price and total_sessions:
            expected_total = session_price * total_sessions
            # Allow up to 1% difference or 10,000 won, whichever is larger
            tolerance = max(float(total_amount) * 0.01, 10000)
            
            if abs(float(total_amount) - float(expected_total)) > tolerance:
                # If difference is significant, auto-adjust session price
                adjusted_price = round(float(total_amount) / total_sessions)
                cleaned_data['session_price'] = Decimal(str(adjusted_price))
        
        return cleaned_data


class SessionForm(forms.ModelForm):
    """Form for scheduling individual sessions"""
    
    class Meta:
        model = Session
        fields = [
            'client', 'package', 'session_date', 'session_time', 
            'session_duration', 'session_cost', 'notes'
        ]
        
        widgets = {
            'client': forms.Select(
                attrs={
                    'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                    'x-model': 'selectedClient',
                    '@change': 'loadClientPackages()'
                }
            ),
            'package': forms.Select(
                attrs={
                    'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                    'x-model': 'selectedPackage',
                    '@change': 'packageChanged()'
                }
            ),
            'session_date': forms.DateInput(
                attrs={
                    'type': 'date',
                    'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                    'min': timezone.now().strftime('%Y-%m-%d')
                }
            ),
            'session_time': forms.TimeInput(
                attrs={
                    'type': 'time',
                    'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
                }
            ),
            'session_duration': forms.NumberInput(
                attrs={
                    'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                    'min': '15',
                    'step': '15',
                    'placeholder': '분'
                }
            ),
            'session_cost': forms.NumberInput(
                attrs={
                    'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 bg-gray-100',
                    'x-model': 'sessionCost',
                    'readonly': True
                }
            ),
            'notes': forms.Textarea(
                attrs={
                    'rows': 2,
                    'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                    'placeholder': '세션 관련 메모 (선택사항)'
                }
            ),
        }
        
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        client_id = kwargs.pop('client_id', None)
        super().__init__(*args, **kwargs)
        
        if user:
            self.fields['client'].queryset = Client.objects.filter(trainer=user)
            
        # Filter packages based on client
        if client_id:
            self.fields['package'].queryset = SessionPackage.objects.filter(
                client_id=client_id, 
                trainer=user,
                is_active=True,
                remaining_sessions__gt=0
            )
        else:
            # If no client_id provided but form has data, try to get client from POST data
            if self.data:
                try:
                    client_id = int(self.data.get('client'))
                    self.fields['package'].queryset = SessionPackage.objects.filter(
                        client_id=client_id, 
                        trainer=user,
                        is_active=True,
                        remaining_sessions__gt=0
                    )
                except (ValueError, TypeError):
                    self.fields['package'].queryset = SessionPackage.objects.none()
            else:
                self.fields['package'].queryset = SessionPackage.objects.none()
            
        # Set default duration
        self.fields['session_duration'].initial = 60
        
    def clean_session_date(self):
        session_date = self.cleaned_data.get('session_date')
        if session_date and session_date < timezone.now().date():
            raise ValidationError("세션 날짜는 과거일 수 없습니다.")
        return session_date
        
    def clean(self):
        cleaned_data = super().clean()
        package = cleaned_data.get('package')
        
        if package and package.remaining_sessions <= 0:
            raise ValidationError("선택한 패키지에 남은 세션이 없습니다.")
            
        return cleaned_data


class PaymentForm(forms.ModelForm):
    """Form for recording payments"""
    
    class Meta:
        model = Payment
        fields = [
            'client', 'package', 'amount', 'payment_method', 
            'payment_date', 'description'
        ]
        
        widgets = {
            'client': forms.Select(
                attrs={
                    'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                    'x-model': 'selectedClient',
                    '@change': 'loadClientPackages()'
                }
            ),
            'package': forms.Select(
                attrs={
                    'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                    'x-model': 'selectedPackage'
                }
            ),
            'amount': forms.NumberInput(
                attrs={
                    'class': 'w-full pl-8 pr-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                    'placeholder': '원',
                    'step': '1000',
                    'min': '0'
                }
            ),
            'payment_method': forms.Select(
                attrs={
                    'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
                }
            ),
            'payment_date': forms.DateInput(
                attrs={
                    'type': 'date',
                    'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                    'max': timezone.now().strftime('%Y-%m-%d')
                }
            ),
            'description': forms.Textarea(
                attrs={
                    'rows': 2,
                    'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                    'placeholder': '결제 관련 메모 (선택사항)'
                }
            ),
        }
        
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user:
            self.fields['client'].queryset = Client.objects.filter(trainer=user)
            
        # Set default payment date to today
        self.fields['payment_date'].initial = timezone.now().date()


class SessionSearchForm(forms.Form):
    """Form for searching and filtering sessions"""
    
    search = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': '회원 이름 또는 패키지명으로 검색...',
            'hx-get': '',
            'hx-trigger': 'keyup changed delay:500ms',
            'hx-target': '#session-list',
            'hx-swap': 'innerHTML',
            'hx-indicator': '#search-indicator'
        })
    )
    
    status = forms.ChoiceField(
        choices=[('', '전체 상태')] + Session.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'hx-get': '',
            'hx-trigger': 'change',
            'hx-target': '#session-list',
            'hx-swap': 'innerHTML'
        })
    )
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'hx-get': '',
            'hx-trigger': 'change',
            'hx-target': '#session-list',
            'hx-swap': 'innerHTML'
        })
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'hx-get': '',
            'hx-trigger': 'change',
            'hx-target': '#session-list',
            'hx-swap': 'innerHTML'
        })
    )