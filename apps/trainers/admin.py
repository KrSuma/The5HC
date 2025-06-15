from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from .models import Organization, Trainer, TrainerInvitation


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'phone', 'email', 'trainer_count', 'max_trainers', 'created_at']
    list_filter = ['created_at', 'max_trainers']
    search_fields = ['name', 'email', 'phone']
    readonly_fields = ['created_at', 'updated_at', 'trainer_count']
    prepopulated_fields = {'slug': ('name',)}
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': ('name', 'slug', 'description')
        }),
        (_('Contact Information'), {
            'fields': ('phone', 'email', 'address')
        }),
        (_('Business Settings'), {
            'fields': ('business_hours', 'timezone', 'max_trainers')
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def trainer_count(self, obj):
        count = obj.get_trainer_count()
        return f"{count} / {obj.max_trainers}"
    trainer_count.short_description = _('Trainers')


@admin.register(Trainer)
class TrainerAdmin(admin.ModelAdmin):
    list_display = ['get_display_name', 'organization', 'role', 'is_active', 
                    'years_of_experience', 'session_price', 'created_at']
    list_filter = ['role', 'is_active', 'organization', 'years_of_experience']
    search_fields = ['user__first_name', 'user__last_name', 'user__email', 
                     'organization__name', 'bio']
    readonly_fields = ['created_at', 'updated_at', 'deactivated_at']
    raw_id_fields = ['user']
    
    fieldsets = (
        (_('User Account'), {
            'fields': ('user', 'organization', 'role')
        }),
        (_('Profile Information'), {
            'fields': ('bio', 'profile_photo', 'years_of_experience')
        }),
        (_('Professional Information'), {
            'fields': ('certifications', 'specialties')
        }),
        (_('Business Settings'), {
            'fields': ('session_price', 'availability_schedule')
        }),
        (_('Status'), {
            'fields': ('is_active', 'deactivated_at')
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['activate_trainers', 'deactivate_trainers']
    
    def get_display_name(self, obj):
        return obj.get_display_name()
    get_display_name.short_description = _('Name')
    get_display_name.admin_order_field = 'user__first_name'
    
    def activate_trainers(self, request, queryset):
        for trainer in queryset:
            trainer.reactivate()
        self.message_user(request, _('Selected trainers have been activated.'))
    activate_trainers.short_description = _('Activate selected trainers')
    
    def deactivate_trainers(self, request, queryset):
        for trainer in queryset:
            trainer.deactivate()
        self.message_user(request, _('Selected trainers have been deactivated.'))
    deactivate_trainers.short_description = _('Deactivate selected trainers')


@admin.register(TrainerInvitation)
class TrainerInvitationAdmin(admin.ModelAdmin):
    list_display = ['email', 'organization', 'role', 'status', 'invited_by', 
                    'created_at', 'expires_at', 'status_badge']
    list_filter = ['status', 'role', 'organization', 'created_at', 'expires_at']
    search_fields = ['email', 'first_name', 'last_name', 'organization__name', 
                     'invited_by__email']
    readonly_fields = ['invitation_code', 'created_at', 'accepted_at', 'status_badge']
    raw_id_fields = ['invited_by']
    
    fieldsets = (
        (_('Invitation Details'), {
            'fields': ('organization', 'email', 'first_name', 'last_name', 'role')
        }),
        (_('Invitation Message'), {
            'fields': ('message',)
        }),
        (_('Metadata'), {
            'fields': ('invited_by', 'invitation_code', 'status', 'expires_at')
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'accepted_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['resend_invitations', 'mark_as_expired']
    
    def status_badge(self, obj):
        colors = {
            'pending': 'orange',
            'accepted': 'green',
            'declined': 'red',
            'expired': 'gray'
        }
        return format_html(
            '<span style="color: {};">{}</span>',
            colors.get(obj.status, 'black'),
            obj.get_status_display()
        )
    status_badge.short_description = _('Status')
    
    def resend_invitations(self, request, queryset):
        # This would typically trigger email sending
        pending_invitations = queryset.filter(status='pending')
        count = pending_invitations.count()
        self.message_user(
            request, 
            _(f'{count} invitation(s) would be resent (email functionality not implemented).')
        )
    resend_invitations.short_description = _('Resend selected invitations')
    
    def mark_as_expired(self, request, queryset):
        queryset.update(status='expired')
        self.message_user(request, _('Selected invitations marked as expired.'))
    mark_as_expired.short_description = _('Mark as expired')
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Automatically check for expired invitations
        TrainerInvitation.check_expired()
        return qs
