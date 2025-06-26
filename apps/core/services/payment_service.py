"""
Payment service handling all business logic related to payments and packages.
"""
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Tuple, Any

from django.db import transaction
from django.db.models import Q, Sum, Count, Avg, F
from django.db.models.query import QuerySet
from django.utils import timezone

from .base import BaseService
from apps.sessions.models import SessionPackage, Session, Payment, FeeAuditLog
from apps.clients.models import Client


class PaymentService(BaseService):
    """
    Service class for payment and session package related business logic.
    
    This service handles:
    - Session package creation and management
    - Payment processing
    - Fee calculations (VAT, card processing)
    - Financial reporting
    """
    
    model = SessionPackage
    
    # Standard fee rates
    VAT_RATE = Decimal('0.10')  # 10% VAT
    CARD_FEE_RATE = Decimal('0.035')  # 3.5% card processing fee
    
    def calculate_fees(self, gross_amount: Decimal) -> Dict[str, Decimal]:
        """
        Calculate VAT and card processing fees from gross amount.
        
        The gross amount includes all fees. We need to extract:
        - Base amount
        - VAT (10%)
        - Card fee (3.5%)
        
        Formula:
        gross_amount = base_amount + vat + card_fee
        gross_amount = base_amount + (base_amount * 0.10) + (base_amount * 0.035)
        gross_amount = base_amount * 1.135
        base_amount = gross_amount / 1.135
        
        Args:
            gross_amount: Total amount including all fees
            
        Returns:
            Dictionary with fee breakdown
        """
        gross_amount = Decimal(str(gross_amount))
        
        # Calculate base amount (before fees)
        total_rate = Decimal('1') + self.VAT_RATE + self.CARD_FEE_RATE
        base_amount = gross_amount / total_rate
        
        # Calculate individual fees
        vat_amount = base_amount * self.VAT_RATE
        card_fee = base_amount * self.CARD_FEE_RATE
        
        # Net amount is base amount (after all fees removed)
        net_amount = base_amount
        
        # Verify calculation
        calculated_gross = base_amount + vat_amount + card_fee
        
        return {
            'gross_amount': gross_amount,
            'base_amount': base_amount.quantize(Decimal('0.01')),
            'vat_amount': vat_amount.quantize(Decimal('0.01')),
            'card_fee': card_fee.quantize(Decimal('0.01')),
            'net_amount': net_amount.quantize(Decimal('0.01')),
            'vat_rate': self.VAT_RATE,
            'card_fee_rate': self.CARD_FEE_RATE,
            'calculated_gross': calculated_gross.quantize(Decimal('0.01'))
        }
    
    def create_session_package(self, data: Dict[str, Any]) -> Tuple[Optional[SessionPackage], bool]:
        """
        Create a new session package with fee calculations.
        
        Args:
            data: Package data including client_id, package_name, total_sessions, total_amount
            
        Returns:
            Tuple of (package, success)
        """
        self.clear_errors()
        
        # Validate required fields
        required_fields = ['client_id', 'package_name', 'total_sessions', 'total_amount']
        for field in required_fields:
            if field not in data or data[field] is None:
                self.add_error(f"{field}는 필수 입력 항목입니다.")
        
        if self.has_errors:
            return None, False
        
        # Get client
        try:
            client = Client.objects.get(
                pk=data['client_id'],
                trainer__trainer__organization=self.organization
            )
        except Client.DoesNotExist:
            self.add_error("고객을 찾을 수 없습니다.")
            return None, False
        
        # Calculate fees
        fee_breakdown = self.calculate_fees(data['total_amount'])
        
        try:
            with transaction.atomic():
                # Create package
                package = SessionPackage(
                    client=client,
                    trainer=self.user,
                    package_name=data['package_name'],
                    total_sessions=data['total_sessions'],
                    remaining_sessions=data['total_sessions'],
                    total_amount=fee_breakdown['gross_amount'],
                    vat_amount=fee_breakdown['vat_amount'],
                    card_fee=fee_breakdown['card_fee'],
                    net_amount=fee_breakdown['net_amount'],
                    start_date=data.get('start_date', timezone.now().date()),
                    end_date=data.get('end_date'),
                    is_active=True
                )
                
                # Save with audit
                if self.save_with_audit(package, action='create'):
                    # Log fee calculation
                    self._log_fee_audit(package, fee_breakdown)
                    return package, True
                else:
                    return None, False
                    
        except Exception as e:
            self.add_error(f"패키지 생성 중 오류가 발생했습니다: {str(e)}")
            return None, False
    
    def _log_fee_audit(self, package: SessionPackage, fee_breakdown: Dict[str, Decimal]) -> None:
        """Log fee calculation for audit trail."""
        try:
            FeeAuditLog.objects.create(
                session_package=package,
                gross_amount=fee_breakdown['gross_amount'],
                vat_amount=fee_breakdown['vat_amount'],
                vat_rate=fee_breakdown['vat_rate'],
                card_fee=fee_breakdown['card_fee'],
                card_fee_rate=fee_breakdown['card_fee_rate'],
                net_amount=fee_breakdown['net_amount'],
                created_by=self.user
            )
        except Exception as e:
            # Don't fail the transaction for audit log failure
            logger.error(f"Failed to create fee audit log: {e}")
    
    def record_payment(self, package: SessionPackage, amount: Decimal, 
                      payment_method: str = 'card',
                      notes: Optional[str] = None) -> Tuple[Optional[Payment], bool]:
        """
        Record a payment for a session package.
        
        Args:
            package: SessionPackage instance
            amount: Payment amount
            payment_method: Payment method (card, cash, transfer)
            notes: Optional payment notes
            
        Returns:
            Tuple of (payment, success)
        """
        self.clear_errors()
        
        # Check permission
        if not self.check_permission(package, 'edit'):
            self.add_error("이 패키지에 대한 권한이 없습니다.")
            return None, False
        
        # Validate amount
        if amount <= 0:
            self.add_error("결제 금액은 0보다 커야 합니다.")
            return None, False
        
        # Check if payment exceeds remaining balance
        total_paid = package.payments.aggregate(Sum('amount'))['amount__sum'] or Decimal('0')
        remaining = package.total_amount - total_paid
        
        if amount > remaining:
            self.add_error(f"결제 금액이 잔액({remaining:,.0f}원)을 초과합니다.")
            return None, False
        
        try:
            with transaction.atomic():
                payment = Payment(
                    session_package=package,
                    amount=amount,
                    payment_method=payment_method,
                    payment_date=timezone.now(),
                    notes=notes,
                    trainer=self.user
                )
                
                if self.save_with_audit(payment, action='create'):
                    # Update package paid status if fully paid
                    total_paid += amount
                    if total_paid >= package.total_amount:
                        package.is_paid = True
                        package.save()
                    
                    return payment, True
                else:
                    return None, False
                    
        except Exception as e:
            self.add_error(f"결제 기록 중 오류가 발생했습니다: {str(e)}")
            return None, False
    
    def use_session(self, package: SessionPackage, 
                   session_date: Optional[date] = None,
                   notes: Optional[str] = None) -> Tuple[Optional[Session], bool]:
        """
        Use a session from a package.
        
        Args:
            package: SessionPackage to use session from
            session_date: Date of the session (defaults to today)
            notes: Optional session notes
            
        Returns:
            Tuple of (session, success)
        """
        self.clear_errors()
        
        # Check permission
        if not self.check_permission(package, 'edit'):
            self.add_error("이 패키지에 대한 권한이 없습니다.")
            return None, False
        
        # Check if package is active
        if not package.is_active:
            self.add_error("비활성 패키지입니다.")
            return None, False
        
        # Check remaining sessions
        if package.remaining_sessions <= 0:
            self.add_error("남은 세션이 없습니다.")
            return None, False
        
        # Check expiry
        if package.end_date and package.end_date < timezone.now().date():
            self.add_error("만료된 패키지입니다.")
            return None, False
        
        try:
            with transaction.atomic():
                # Create session
                session = Session(
                    client=package.client,
                    session_package=package,
                    session_date=session_date or timezone.now().date(),
                    session_type='PT',  # Default to PT
                    status='completed',
                    notes=notes,
                    trainer=self.user
                )
                
                if self.save_with_audit(session, action='create'):
                    # Decrement remaining sessions
                    package.remaining_sessions = F('remaining_sessions') - 1
                    package.save(update_fields=['remaining_sessions'])
                    
                    # Refresh to get updated value
                    package.refresh_from_db()
                    
                    # Deactivate if no sessions left
                    if package.remaining_sessions == 0:
                        package.is_active = False
                        package.save(update_fields=['is_active'])
                    
                    return session, True
                else:
                    return None, False
                    
        except Exception as e:
            self.add_error(f"세션 사용 중 오류가 발생했습니다: {str(e)}")
            return None, False
    
    def cancel_session(self, session: Session, reason: Optional[str] = None) -> bool:
        """
        Cancel a session and restore it to the package.
        
        Args:
            session: Session to cancel
            reason: Cancellation reason
            
        Returns:
            bool: True if successful
        """
        self.clear_errors()
        
        # Check permission
        if not self.check_permission(session, 'edit'):
            self.add_error("이 세션에 대한 권한이 없습니다.")
            return False
        
        # Check if already cancelled
        if session.status == 'cancelled':
            self.add_error("이미 취소된 세션입니다.")
            return False
        
        try:
            with transaction.atomic():
                # Update session status
                session.status = 'cancelled'
                session.notes = f"{session.notes}\n취소 사유: {reason}" if reason else session.notes
                
                if self.save_with_audit(session, action='update', 
                                       metadata={'reason': reason}):
                    # Restore session to package
                    if session.session_package:
                        package = session.session_package
                        package.remaining_sessions = F('remaining_sessions') + 1
                        package.is_active = True  # Reactivate if was inactive
                        package.save(update_fields=['remaining_sessions', 'is_active'])
                    
                    return True
                else:
                    return False
                    
        except Exception as e:
            self.add_error(f"세션 취소 중 오류가 발생했습니다: {str(e)}")
            return False
    
    def get_package_statistics(self, package: SessionPackage) -> Dict[str, Any]:
        """
        Get comprehensive statistics for a session package.
        
        Args:
            package: SessionPackage instance
            
        Returns:
            Dictionary of statistics
        """
        stats = {
            'total_sessions': package.total_sessions,
            'used_sessions': package.total_sessions - package.remaining_sessions,
            'remaining_sessions': package.remaining_sessions,
            'usage_rate': (
                ((package.total_sessions - package.remaining_sessions) / package.total_sessions * 100)
                if package.total_sessions > 0 else 0
            ),
            'days_until_expiry': None,
            'is_expired': False
        }
        
        # Calculate days until expiry
        if package.end_date:
            days_until = (package.end_date - timezone.now().date()).days
            stats['days_until_expiry'] = days_until
            stats['is_expired'] = days_until < 0
        
        # Payment statistics
        payment_stats = package.payments.aggregate(
            total_paid=Sum('amount'),
            payment_count=Count('id'),
            last_payment_date=Max('payment_date')
        )
        
        stats['total_paid'] = payment_stats['total_paid'] or Decimal('0')
        stats['payment_count'] = payment_stats['payment_count']
        stats['last_payment_date'] = payment_stats['last_payment_date']
        stats['remaining_balance'] = package.total_amount - stats['total_paid']
        stats['payment_completion_rate'] = (
            (stats['total_paid'] / package.total_amount * 100)
            if package.total_amount > 0 else 0
        )
        
        # Session statistics
        session_stats = package.sessions.aggregate(
            completed_count=Count('id', filter=Q(status='completed')),
            cancelled_count=Count('id', filter=Q(status='cancelled')),
            last_session_date=Max('session_date')
        )
        stats.update(session_stats)
        
        return stats
    
    def get_financial_summary(self, start_date: Optional[date] = None,
                            end_date: Optional[date] = None) -> Dict[str, Any]:
        """
        Get financial summary for the organization.
        
        Args:
            start_date: Start date for the period
            end_date: End date for the period
            
        Returns:
            Dictionary of financial metrics
        """
        # Default to current month if no dates provided
        if not start_date:
            start_date = timezone.now().replace(day=1).date()
        if not end_date:
            end_date = timezone.now().date()
        
        # Filter packages by date range
        packages = self.get_queryset().filter(
            created_at__date__gte=start_date,
            created_at__date__lte=end_date
        )
        
        # Calculate metrics
        summary = packages.aggregate(
            total_packages=Count('id'),
            total_gross_revenue=Sum('total_amount'),
            total_net_revenue=Sum('net_amount'),
            total_vat=Sum('vat_amount'),
            total_card_fees=Sum('card_fee'),
            avg_package_value=Avg('total_amount'),
            total_sessions_sold=Sum('total_sessions')
        )
        
        # Payment metrics
        payments = Payment.objects.filter(
            session_package__trainer__trainer__organization=self.organization,
            payment_date__date__gte=start_date,
            payment_date__date__lte=end_date
        )
        
        payment_summary = payments.aggregate(
            total_collected=Sum('amount'),
            payment_count=Count('id'),
            avg_payment=Avg('amount')
        )
        
        summary.update(payment_summary)
        
        # Calculate collection rate
        if summary['total_gross_revenue']:
            summary['collection_rate'] = (
                (summary['total_collected'] or 0) / summary['total_gross_revenue'] * 100
            )
        else:
            summary['collection_rate'] = 0
        
        # Active packages
        summary['active_packages'] = self.get_queryset().filter(
            is_active=True,
            remaining_sessions__gt=0
        ).count()
        
        # Sessions conducted
        sessions = Session.objects.filter(
            trainer__trainer__organization=self.organization,
            session_date__gte=start_date,
            session_date__lte=end_date
        )
        
        session_summary = sessions.aggregate(
            total_sessions_conducted=Count('id', filter=Q(status='completed')),
            cancelled_sessions=Count('id', filter=Q(status='cancelled'))
        )
        
        summary.update(session_summary)
        
        return summary
    
    def get_expiring_packages(self, days_ahead: int = 30) -> QuerySet:
        """
        Get packages expiring within specified days.
        
        Args:
            days_ahead: Number of days to look ahead
            
        Returns:
            QuerySet of expiring packages
        """
        cutoff_date = timezone.now().date() + timedelta(days=days_ahead)
        
        return self.get_queryset().filter(
            is_active=True,
            end_date__lte=cutoff_date,
            end_date__gte=timezone.now().date()
        ).select_related('client', 'trainer')
    
    def get_payment_due_packages(self) -> QuerySet:
        """
        Get packages with outstanding payments.
        
        Returns:
            QuerySet of packages with payment due
        """
        packages = self.get_queryset().filter(is_active=True)
        
        # Annotate with payment info
        packages = packages.annotate(
            total_paid=Sum('payments__amount'),
            payment_due=F('total_amount') - F('total_paid')
        )
        
        # Filter for those with outstanding balance
        return packages.filter(payment_due__gt=0).select_related('client', 'trainer')