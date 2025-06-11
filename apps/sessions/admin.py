from django.contrib import admin
from django.utils.html import format_html
from decimal import Decimal
from .models import SessionPackage, Session, Payment, FeeAuditLog


class SessionInline(admin.TabularInline):
    """Inline admin for sessions within a package."""
    model = Session
    extra = 0
    fields = ['session_date', 'session_time', 'session_duration', 
              'session_cost', 'status', 'notes']
    readonly_fields = ['created_at']
    ordering = ['-session_date']


class PaymentInline(admin.TabularInline):
    """Inline admin for payments within a package."""
    model = Payment
    extra = 0
    fields = ['payment_date', 'amount', 'payment_method', 
              'gross_amount', 'net_amount']
    readonly_fields = ['gross_amount', 'vat_amount', 
                      'card_fee_amount', 'net_amount']


@admin.register(SessionPackage)
class SessionPackageAdmin(admin.ModelAdmin):
    """
    Admin configuration for SessionPackage model.
    """
    list_display = [
        'display_package_name', 'client', 'trainer', 
        'display_sessions', 'display_amounts', 'is_active', 
        'created_at'
    ]
    list_filter = [
        'is_active', 'trainer', 'created_at', 'total_sessions'
    ]
    search_fields = ['client__name', 'package_name', 'trainer__username']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('client', 'trainer', 'package_name', 'is_active')
        }),
        ('패키지 상세', {
            'fields': (
                'total_sessions', 'remaining_sessions',
                'session_price', 'total_amount',
                'remaining_credits', 'notes'
            )
        }),
        ('수수료 정보', {
            'fields': (
                'fee_calculation_method', 'vat_rate', 'card_fee_rate',
                'gross_amount', 'vat_amount', 'card_fee_amount', 'net_amount'
            ),
            'classes': ('collapse',),
            'description': 'VAT 및 카드 수수료 계산 정보'
        }),
    )
    
    readonly_fields = [
        'created_at', 'updated_at', 'gross_amount', 
        'vat_amount', 'card_fee_amount', 'net_amount'
    ]
    
    inlines = [SessionInline, PaymentInline]
    
    def display_package_name(self, obj):
        """Display package name with fallback."""
        return obj.package_name or f"패키지 #{obj.id}"
    display_package_name.short_description = '패키지명'
    
    def display_sessions(self, obj):
        """Display session progress."""
        return f"{obj.remaining_sessions}/{obj.total_sessions}"
    display_sessions.short_description = '남은/전체 세션'
    
    def display_amounts(self, obj):
        """Display financial summary."""
        return format_html(
            '<strong>총액:</strong> ₩{:,}<br>'
            '<strong>순액:</strong> ₩{:,}',
            int(obj.total_amount),
            obj.net_amount or 0
        )
    display_amounts.short_description = '금액 정보'
    
    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        qs = super().get_queryset(request)
        return qs.select_related('client', 'trainer')
    
    def save_model(self, request, obj, form, change):
        """Calculate fees before saving."""
        if not obj.gross_amount:
            obj.calculate_fees(save_audit=True)
        super().save_model(request, obj, form, change)


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    """
    Admin configuration for Session model.
    """
    list_display = [
        'client', 'session_date', 'session_time', 'trainer',
        'session_duration', 'session_cost', 'status', 'package'
    ]
    list_filter = [
        'status', 'session_date', 'trainer', 'session_duration'
    ]
    search_fields = ['client__name', 'trainer__username', 'notes']
    ordering = ['-session_date', '-session_time']
    date_hierarchy = 'session_date'
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('client', 'trainer', 'package')
        }),
        ('세션 상세', {
            'fields': (
                'session_date', 'session_time', 
                'session_duration', 'session_cost'
            )
        }),
        ('상태 및 노트', {
            'fields': ('status', 'notes', 'completed_at')
        }),
    )
    
    readonly_fields = ['created_at', 'completed_at']
    
    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        qs = super().get_queryset(request)
        return qs.select_related('client', 'trainer', 'package')
    
    actions = ['mark_completed', 'mark_cancelled']
    
    def mark_completed(self, request, queryset):
        """Mark selected sessions as completed."""
        from django.utils import timezone
        updated = queryset.update(
            status='completed',
            completed_at=timezone.now()
        )
        self.message_user(request, f'{updated}개 세션이 완료됨으로 표시되었습니다.')
    mark_completed.short_description = '선택한 세션을 완료됨으로 표시'
    
    def mark_cancelled(self, request, queryset):
        """Mark selected sessions as cancelled."""
        updated = queryset.update(status='cancelled')
        self.message_user(request, f'{updated}개 세션이 취소됨으로 표시되었습니다.')
    mark_cancelled.short_description = '선택한 세션을 취소됨으로 표시'


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """
    Admin configuration for Payment model.
    """
    list_display = [
        'client', 'payment_date', 'display_amount', 
        'payment_method', 'trainer', 'package'
    ]
    list_filter = [
        'payment_method', 'payment_date', 'trainer'
    ]
    search_fields = ['client__name', 'trainer__username', 'description']
    ordering = ['-payment_date', '-created_at']
    date_hierarchy = 'payment_date'
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('client', 'trainer', 'package')
        }),
        ('결제 정보', {
            'fields': (
                'payment_date', 'amount', 'payment_method',
                'description'
            )
        }),
        ('수수료 정보', {
            'fields': (
                'vat_rate', 'card_fee_rate',
                'gross_amount', 'vat_amount', 
                'card_fee_amount', 'net_amount'
            ),
            'classes': ('collapse',),
            'description': 'VAT 및 카드 수수료 계산 정보'
        }),
    )
    
    readonly_fields = [
        'created_at', 'gross_amount', 'vat_amount', 
        'card_fee_amount', 'net_amount'
    ]
    
    def display_amount(self, obj):
        """Display formatted amount with fee info."""
        if obj.net_amount:
            return format_html(
                '₩{:,}<br><small>순액: ₩{:,}</small>',
                int(obj.amount),
                obj.net_amount
            )
        return f"₩{int(obj.amount):,}"
    display_amount.short_description = '금액'
    
    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        qs = super().get_queryset(request)
        return qs.select_related('client', 'trainer', 'package')


@admin.register(FeeAuditLog)
class FeeAuditLogAdmin(admin.ModelAdmin):
    """
    Admin configuration for FeeAuditLog model.
    """
    list_display = [
        'created_at', 'created_by', 'calculation_type',
        'display_target', 'display_amounts', 'display_rates'
    ]
    list_filter = [
        'calculation_type', 'created_at', 'created_by'
    ]
    search_fields = ['created_by__username', 'calculation_details']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('감사 정보', {
            'fields': ('created_by', 'created_at', 'calculation_type')
        }),
        ('대상', {
            'fields': ('package', 'payment')
        }),
        ('계산 상세', {
            'fields': (
                'gross_amount', 'vat_amount', 
                'card_fee_amount', 'net_amount',
                'vat_rate', 'card_fee_rate',
                'calculation_details'
            )
        }),
    )
    
    readonly_fields = [
        'created_at', 'created_by', 'package', 'payment',
        'gross_amount', 'vat_amount', 'card_fee_amount', 
        'net_amount', 'vat_rate', 'card_fee_rate',
        'calculation_details', 'calculation_type'
    ]
    
    def display_target(self, obj):
        """Display the target of the audit log."""
        if obj.package:
            return f"패키지: {obj.package}"
        elif obj.payment:
            return f"결제: {obj.payment}"
        return "-"
    display_target.short_description = '대상'
    
    def display_amounts(self, obj):
        """Display amount breakdown."""
        return format_html(
            '총액: ₩{:,}<br>'
            'VAT: ₩{:,}<br>'
            '카드수수료: ₩{:,}<br>'
            '<strong>순액: ₩{:,}</strong>',
            obj.gross_amount,
            obj.vat_amount,
            obj.card_fee_amount,
            obj.net_amount
        )
    display_amounts.short_description = '금액 내역'
    
    def display_rates(self, obj):
        """Display rate information."""
        return format_html(
            'VAT: {}%<br>카드: {}%',
            obj.vat_rate * 100,
            obj.card_fee_rate * 100
        )
    display_rates.short_description = '수수료율'
    
    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        qs = super().get_queryset(request)
        return qs.select_related(
            'created_by', 'package__client', 'payment__client'
        )
    
    def has_add_permission(self, request):
        """Disable manual creation of audit logs."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Disable editing of audit logs."""
        return False
