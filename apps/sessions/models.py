from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from decimal import Decimal
import json


class SessionPackage(models.Model):
    """
    Session package model for managing client training packages.
    Includes fee calculations for VAT and card processing.
    """
    # Relationships
    client = models.ForeignKey(
        'clients.Client',
        on_delete=models.CASCADE,
        related_name='session_packages'
    )
    trainer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='session_packages'
    )
    
    # Package details
    package_name = models.CharField(max_length=200, blank=True, null=True)
    total_amount = models.DecimalField(
        max_digits=10, decimal_places=2,
        help_text="Original total amount in KRW"
    )
    session_price = models.DecimalField(
        max_digits=10, decimal_places=2,
        help_text="Price per session in KRW"
    )
    total_sessions = models.IntegerField(validators=[MinValueValidator(1)])
    remaining_sessions = models.IntegerField(validators=[MinValueValidator(0)])
    remaining_credits = models.DecimalField(
        max_digits=10, decimal_places=2,
        help_text="Remaining monetary credits in KRW"
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True, null=True)
    
    # Fee-related fields
    gross_amount = models.IntegerField(
        null=True, blank=True,
        help_text="Gross amount including all fees"
    )
    vat_amount = models.IntegerField(
        null=True, blank=True,
        help_text="VAT amount"
    )
    card_fee_amount = models.IntegerField(
        null=True, blank=True,
        help_text="Card processing fee amount"
    )
    net_amount = models.IntegerField(
        null=True, blank=True,
        help_text="Net amount after fees"
    )
    vat_rate = models.DecimalField(
        max_digits=5, decimal_places=2,
        default=Decimal('0.10')
    )
    card_fee_rate = models.DecimalField(
        max_digits=5, decimal_places=2,
        default=Decimal('0.035')
    )
    fee_calculation_method = models.CharField(
        max_length=20,
        default='inclusive',
        choices=[
            ('inclusive', 'Inclusive'),
            ('exclusive', 'Exclusive')
        ]
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'session_packages'
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.client.name} - {self.package_name or 'Package'} ({self.remaining_sessions}/{self.total_sessions})"
    
    def calculate_fees(self, save_audit=True):
        """
        Calculate VAT and card processing fees.
        Uses inclusive calculation method (fees included in gross amount).
        """
        if self.fee_calculation_method == 'inclusive':
            # For inclusive calculation
            gross = int(self.total_amount)
            total_fee_rate = self.vat_rate + self.card_fee_rate
            net = int(gross / (1 + total_fee_rate))
            vat = int(net * self.vat_rate)
            card_fee = int(net * self.card_fee_rate)
            
            # Adjust for rounding
            total_fees = vat + card_fee
            if gross - net != total_fees:
                card_fee += gross - net - total_fees
        else:
            # For exclusive calculation (not currently used)
            net = int(self.total_amount)
            vat = int(net * self.vat_rate)
            card_fee = int(net * self.card_fee_rate)
            gross = net + vat + card_fee
        
        self.gross_amount = gross
        self.vat_amount = vat
        self.card_fee_amount = card_fee
        self.net_amount = net
        
        if save_audit:
            FeeAuditLog.objects.create(
                package=self,
                calculation_type='inclusive',
                gross_amount=gross,
                vat_amount=vat,
                card_fee_amount=card_fee,
                net_amount=net,
                vat_rate=self.vat_rate,
                card_fee_rate=self.card_fee_rate,
                calculation_details=json.dumps({
                    'original_amount': float(self.total_amount),
                    'method': self.fee_calculation_method,
                    'total_fee_rate': float(self.vat_rate + self.card_fee_rate)
                }),
                created_by=self.trainer
            )
    
    def save(self, *args, **kwargs):
        """Override save to calculate fees if not already set."""
        if self.gross_amount is None:
            self.calculate_fees(save_audit=False)
        super().save(*args, **kwargs)


class Session(models.Model):
    """
    Individual training session model.
    """
    STATUS_CHOICES = [
        ('scheduled', '예약됨'),
        ('completed', '완료됨'),
        ('cancelled', '취소됨'),
    ]
    
    # Relationships
    client = models.ForeignKey(
        'clients.Client',
        on_delete=models.CASCADE,
        related_name='sessions'
    )
    package = models.ForeignKey(
        SessionPackage,
        on_delete=models.CASCADE,
        related_name='sessions'
    )
    trainer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sessions'
    )
    
    # Session details
    session_date = models.DateField()
    session_time = models.TimeField(null=True, blank=True)
    session_duration = models.IntegerField(
        validators=[MinValueValidator(1)],
        help_text="Duration in minutes"
    )
    session_cost = models.DecimalField(
        max_digits=10, decimal_places=2,
        help_text="Cost of this session in KRW"
    )
    
    # Status and notes
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='scheduled'
    )
    notes = models.TextField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'sessions'
        ordering = ['-session_date', '-session_time']
        
    def __str__(self):
        return f"{self.client.name} - {self.session_date} ({self.get_status_display()})"


class Payment(models.Model):
    """
    Payment model for tracking client payments.
    """
    PAYMENT_METHOD_CHOICES = [
        ('cash', '현금'),
        ('card', '카드'),
        ('transfer', '계좌이체'),
        ('other', '기타'),
    ]
    
    # Relationships
    client = models.ForeignKey(
        'clients.Client',
        on_delete=models.CASCADE,
        related_name='payments'
    )
    package = models.ForeignKey(
        SessionPackage,
        on_delete=models.CASCADE,
        related_name='payments',
        null=True, blank=True
    )
    trainer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='payments'
    )
    
    # Payment details
    amount = models.DecimalField(
        max_digits=10, decimal_places=2,
        help_text="Original payment amount"
    )
    payment_method = models.CharField(
        max_length=50,
        choices=PAYMENT_METHOD_CHOICES,
        blank=True, null=True
    )
    description = models.TextField(blank=True, null=True)
    payment_date = models.DateField()
    
    # Fee-related fields
    gross_amount = models.IntegerField(null=True, blank=True)
    vat_amount = models.IntegerField(null=True, blank=True)
    card_fee_amount = models.IntegerField(null=True, blank=True)
    net_amount = models.IntegerField(null=True, blank=True)
    vat_rate = models.DecimalField(
        max_digits=5, decimal_places=2,
        null=True, blank=True
    )
    card_fee_rate = models.DecimalField(
        max_digits=5, decimal_places=2,
        null=True, blank=True
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'payments'
        ordering = ['-payment_date', '-created_at']
        
    def __str__(self):
        return f"{self.client.name} - {self.amount}원 ({self.payment_date})"


class FeeAuditLog(models.Model):
    """
    Audit log for fee calculations to track all fee-related operations.
    """
    # Relationships
    package = models.ForeignKey(
        SessionPackage,
        on_delete=models.CASCADE,
        related_name='fee_audit_logs',
        null=True, blank=True
    )
    payment = models.ForeignKey(
        Payment,
        on_delete=models.CASCADE,
        related_name='fee_audit_logs',
        null=True, blank=True
    )
    
    # Calculation details
    calculation_type = models.CharField(max_length=20)
    gross_amount = models.IntegerField()
    vat_amount = models.IntegerField()
    card_fee_amount = models.IntegerField()
    net_amount = models.IntegerField()
    vat_rate = models.DecimalField(max_digits=5, decimal_places=2)
    card_fee_rate = models.DecimalField(max_digits=5, decimal_places=2)
    calculation_details = models.JSONField()
    
    # Audit fields
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='fee_audit_logs'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'fee_audit_log'
        ordering = ['-created_at']
        
    def __str__(self):
        target = self.package or self.payment
        return f"Fee Audit - {target} - {self.created_at}"