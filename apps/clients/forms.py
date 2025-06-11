from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from .models import Client


class ClientForm(forms.ModelForm):
    """Form for creating and editing clients."""
    
    class Meta:
        model = Client
        fields = ['name', 'age', 'gender', 'height', 'weight', 'email', 'phone']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': '회원 이름',
                'hx-post': '/clients/validate/name/',
                'hx-trigger': 'keyup changed delay:500ms',
                'hx-target': '#name-errors',
                'hx-indicator': '.name-indicator',
            }),
            'age': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': '나이',
                'min': '10',
                'max': '100',
            }),
            'gender': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            }),
            'height': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': '키 (cm)',
                'step': '0.1',
                'min': '100',
                'max': '250',
                'x-model.number': 'height',
            }),
            'weight': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': '몸무게 (kg)',
                'step': '0.1',
                'min': '30',
                'max': '200',
                'x-model.number': 'weight',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': '이메일 (선택사항)',
                'hx-post': '/clients/validate/email/',
                'hx-trigger': 'blur',
                'hx-target': '#email-errors',
            }),
            'phone': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': '전화번호 (선택사항)',
                'hx-post': '/clients/validate/phone/',
                'hx-trigger': 'blur',
                'hx-target': '#phone-errors',
            }),
        }
        labels = {
            'name': _('Name'),
            'age': _('Age'),
            'gender': _('Gender'),
            'height': _('Height (cm)'),
            'weight': _('Weight (kg)'),
            'email': _('Email'),
            'phone': _('Phone'),
        }
    
    def __init__(self, *args, **kwargs):
        self.trainer = kwargs.pop('trainer', None)
        super().__init__(*args, **kwargs)
        
    def clean_name(self):
        name = self.cleaned_data.get('name')
        if name and len(name) < 2:
            raise ValidationError(_("Name must be at least 2 characters long"))
        return name
    
    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone:
            # Remove any non-digit characters
            cleaned_phone = ''.join(filter(str.isdigit, phone))
            if len(cleaned_phone) not in [10, 11]:
                raise ValidationError(_("Enter a valid phone number"))
        return phone
    
    def clean(self):
        cleaned_data = super().clean()
        height = cleaned_data.get('height')
        weight = cleaned_data.get('weight')
        
        if height and weight:
            bmi = weight / ((height / 100) ** 2)
            if bmi < 10 or bmi > 50:
                raise ValidationError(_("Please check your height and weight values"))
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.trainer:
            instance.trainer = self.trainer
        if commit:
            instance.save()
        return instance


class ClientSearchForm(forms.Form):
    """Form for searching clients."""
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': '이름, 이메일, 전화번호로 검색...',
            'hx-get': '/clients/',
            'hx-trigger': 'keyup changed delay:500ms',
            'hx-target': '#client-list',
            'hx-indicator': '.search-indicator',
        })
    )
    
    gender = forms.ChoiceField(
        required=False,
        choices=[('', '전체')] + Client.GENDER_CHOICES,
        widget=forms.Select(attrs={
            'class': 'px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'hx-get': '/clients/',
            'hx-trigger': 'change',
            'hx-target': '#client-list',
        })
    )
    
    age_min = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'w-24 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': '최소',
            'min': '10',
            'max': '100',
            'hx-get': '/clients/',
            'hx-trigger': 'change',
            'hx-target': '#client-list',
        })
    )
    
    age_max = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'w-24 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': '최대',
            'min': '10',
            'max': '100',
            'hx-get': '/clients/',
            'hx-trigger': 'change',
            'hx-target': '#client-list',
        })
    )