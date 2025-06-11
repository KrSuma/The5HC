from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from .models import User


class LoginForm(forms.Form):
    """Login form with email/username and password."""
    email_or_username = forms.CharField(
        label=_("Email or Username"),
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': _('Please enter your email or username'),
            'autofocus': True,
        })
    )
    password = forms.CharField(
        label=_("Password"),
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': _('Please enter your password'),
        })
    )
    remember_me = forms.BooleanField(
        label=_("Remember me"),
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500',
        })
    )
    
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        self.user_cache = None
        
    def clean(self):
        email_or_username = self.cleaned_data.get('email_or_username')
        password = self.cleaned_data.get('password')
        
        if email_or_username and password:
            # Try to authenticate with email first
            if '@' in email_or_username:
                try:
                    user = User.objects.get(email=email_or_username)
                    username = user.username
                except User.DoesNotExist:
                    username = None
            else:
                username = email_or_username
            
            if username:
                self.user_cache = authenticate(
                    self.request,
                    username=username,
                    password=password
                )
                
            if self.user_cache is None:
                raise ValidationError(
                    _("Invalid email or username"),
                    code='invalid_login',
                )
            else:
                self.confirm_login_allowed(self.user_cache)
                
        return self.cleaned_data
    
    def confirm_login_allowed(self, user):
        """Check if the user is allowed to log in."""
        if not user.is_active:
            raise ValidationError(
                _("This account is deactivated."),
                code='inactive',
            )
        if user.is_account_locked():
            raise ValidationError(
                _("Account is locked due to too many failed attempts. Please try again later."),
                code='locked',
            )
    
    def get_user(self):
        return self.user_cache


class CustomUserCreationForm(UserCreationForm):
    """Custom user creation form for trainers."""
    
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'name')
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': '사용자명',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': '이메일 주소',
            }),
            'name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': '이름',
            }),
        }
        labels = {
            'username': _('Username'),
            'email': _('Email'),
            'name': _('Name'),
        }


class CustomUserChangeForm(UserChangeForm):
    """Custom user change form for trainers."""
    
    class Meta(UserChangeForm.Meta):
        model = User
        fields = ('username', 'email', 'name')
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            }),
            'name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            }),
        }


class PasswordResetRequestForm(forms.Form):
    """Form for requesting password reset."""
    email = forms.EmailField(
        label=_("Email"),
        max_length=255,
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': _('Enter your registered email'),
        })
    )
    
    def clean_email(self):
        email = self.cleaned_data['email']
        if not User.objects.filter(email=email).exists():
            raise ValidationError(_("No account found with this email address."))
        return email