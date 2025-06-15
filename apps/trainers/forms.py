from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from .models import Trainer, Organization, TrainerInvitation
import json

User = get_user_model()


class TrainerProfileForm(forms.ModelForm):
    """Form for editing trainer profile information."""
    
    # User fields
    first_name = forms.CharField(
        label=_('First Name'),
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': _('First Name'),
        })
    )
    
    last_name = forms.CharField(
        label=_('Last Name'),
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': _('Last Name'),
        })
    )
    
    email = forms.EmailField(
        label=_('Email'),
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': _('Email Address'),
        })
    )
    
    # Certification fields (as text inputs that will be converted to JSON)
    certifications_text = forms.CharField(
        label=_('Certifications'),
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': _('Enter certifications, one per line'),
            'rows': 4,
        }),
        help_text=_('Enter your certifications, one per line')
    )
    
    # Specialties fields (as text inputs that will be converted to JSON)
    specialties_text = forms.CharField(
        label=_('Specialties'),
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': _('Enter specialties, one per line'),
            'rows': 4,
        }),
        help_text=_('Enter your areas of expertise, one per line')
    )
    
    class Meta:
        model = Trainer
        fields = [
            'bio', 'profile_photo', 'years_of_experience',
            'session_price', 'is_active'
        ]
        widgets = {
            'bio': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': _('Tell us about yourself and your training philosophy'),
                'rows': 5,
            }),
            'profile_photo': forms.FileInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'accept': 'image/*',
            }),
            'years_of_experience': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'min': '0',
                'max': '50',
            }),
            'session_price': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'min': '0',
                'step': '1000',
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded',
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Populate user fields if instance exists
        if self.instance and self.instance.pk:
            user = self.instance.user
            self.fields['first_name'].initial = user.first_name
            self.fields['last_name'].initial = user.last_name
            self.fields['email'].initial = user.email
            
            # Convert JSON fields to text
            if self.instance.certifications:
                self.fields['certifications_text'].initial = '\n'.join(self.instance.certifications)
            if self.instance.specialties:
                self.fields['specialties_text'].initial = '\n'.join(self.instance.specialties)
    
    def clean_email(self):
        """Validate email uniqueness."""
        email = self.cleaned_data['email']
        user_qs = User.objects.filter(email=email)
        
        if self.instance and self.instance.pk:
            user_qs = user_qs.exclude(pk=self.instance.user.pk)
        
        if user_qs.exists():
            raise ValidationError(_('This email is already in use.'))
        
        return email
    
    def clean_certifications_text(self):
        """Convert text input to list."""
        text = self.cleaned_data.get('certifications_text', '')
        if text:
            return [line.strip() for line in text.split('\n') if line.strip()]
        return []
    
    def clean_specialties_text(self):
        """Convert text input to list."""
        text = self.cleaned_data.get('specialties_text', '')
        if text:
            return [line.strip() for line in text.split('\n') if line.strip()]
        return []
    
    def save(self, commit=True):
        """Save both user and trainer profile."""
        trainer = super().save(commit=False)
        
        # Update user fields
        user = trainer.user
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        
        # Update JSON fields
        trainer.certifications = self.cleaned_data.get('certifications_text', [])
        trainer.specialties = self.cleaned_data.get('specialties_text', [])
        
        if commit:
            user.save()
            trainer.save()
        
        return trainer


class OrganizationForm(forms.ModelForm):
    """Form for editing organization information."""
    
    class Meta:
        model = Organization
        fields = [
            'name', 'description', 'phone', 'email', 'address',
            'timezone', 'max_trainers'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': _('Organization Name'),
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': _('Brief description of your organization'),
                'rows': 3,
            }),
            'phone': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': _('Phone Number'),
            }),
            'email': forms.EmailInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': _('Contact Email'),
            }),
            'address': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': _('Organization Address'),
                'rows': 3,
            }),
            'timezone': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            }),
            'max_trainers': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'min': '1',
                'max': '100',
            }),
        }


class TrainerInvitationForm(forms.ModelForm):
    """Form for inviting new trainers to an organization."""
    
    class Meta:
        model = TrainerInvitation
        fields = ['email', 'first_name', 'last_name', 'role', 'message']
        widgets = {
            'email': forms.EmailInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': _('Trainer Email Address'),
                'required': True,
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': _('First Name (optional)'),
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': _('Last Name (optional)'),
            }),
            'role': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            }),
            'message': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': _('Add a personal message to the invitation (optional)'),
                'rows': 4,
            }),
        }
    
    def __init__(self, *args, **kwargs):
        self.organization = kwargs.pop('organization', None)
        super().__init__(*args, **kwargs)
    
    def clean_email(self):
        """Validate that the email isn't already in the organization."""
        email = self.cleaned_data['email']
        
        if self.organization:
            # Check if user with this email already exists in the organization
            if User.objects.filter(
                email=email,
                trainer_profile__organization=self.organization
            ).exists():
                raise ValidationError(
                    _('A trainer with this email already exists in your organization.')
                )
            
            # Check for pending invitations
            if TrainerInvitation.objects.filter(
                email=email,
                organization=self.organization,
                status='pending'
            ).exists():
                raise ValidationError(
                    _('An invitation has already been sent to this email address.')
                )
        
        return email