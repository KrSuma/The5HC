"""
Custom managers for Assessment models with optimized queries.
"""
from django.db import models


class AssessmentQuerySet(models.QuerySet):
    """Custom QuerySet for Assessment model with optimized queries."""
    
    def with_all_tests(self):
        """
        Prefetch all related test models to avoid N+1 queries.
        
        This method uses select_related for all OneToOne relationships
        to fetch all test data in a single query.
        """
        return self.select_related(
            'client',
            'trainer',
            'overhead_squat_test',
            'push_up_test',
            'single_leg_balance_test',
            'toe_touch_test',
            'shoulder_mobility_test',
            'farmers_carry_test',
            'harvard_step_test'
        )
    
    def with_client_and_trainer(self):
        """Prefetch only client and trainer data."""
        return self.select_related('client', 'trainer')
    
    def with_test_scores(self):
        """
        Prefetch test data and annotate with calculated scores.
        Useful for list views where we only need scores.
        """
        return self.with_all_tests().annotate(
            has_overhead_squat=models.Exists(
                models.OuterRef('overhead_squat_test')
            ),
            has_push_up=models.Exists(
                models.OuterRef('push_up_test')
            ),
            has_balance=models.Exists(
                models.OuterRef('single_leg_balance_test')
            ),
            has_toe_touch=models.Exists(
                models.OuterRef('toe_touch_test')
            ),
            has_shoulder_mobility=models.Exists(
                models.OuterRef('shoulder_mobility_test')
            ),
            has_farmers_carry=models.Exists(
                models.OuterRef('farmers_carry_test')
            ),
            has_harvard_step=models.Exists(
                models.OuterRef('harvard_step_test')
            )
        )
    
    def for_organization(self, organization):
        """Filter assessments by organization."""
        return self.filter(trainer__organization=organization)
    
    def recent(self, days=30):
        """Get assessments from the last N days."""
        from django.utils import timezone
        from datetime import timedelta
        
        cutoff_date = timezone.now() - timedelta(days=days)
        return self.filter(date__gte=cutoff_date)


class AssessmentManager(models.Manager):
    """Custom manager for Assessment model."""
    
    def get_queryset(self):
        """Return custom QuerySet."""
        return AssessmentQuerySet(self.model, using=self._db)
    
    def with_all_tests(self):
        """Proxy to QuerySet method."""
        return self.get_queryset().with_all_tests()
    
    def with_client_and_trainer(self):
        """Proxy to QuerySet method."""
        return self.get_queryset().with_client_and_trainer()
    
    def with_test_scores(self):
        """Proxy to QuerySet method."""
        return self.get_queryset().with_test_scores()
    
    def for_organization(self, organization):
        """Proxy to QuerySet method."""
        return self.get_queryset().for_organization(organization)