from django.core.management.base import BaseCommand
from django.db import transaction
from apps.assessments.models import Assessment


class Command(BaseCommand):
    help = 'Recalculate scores for all existing assessments'

    def add_arguments(self, parser):
        parser.add_argument(
            '--assessment-id',
            type=int,
            help='Recalculate scores for a specific assessment ID',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes',
        )

    def handle(self, *args, **options):
        assessment_id = options.get('assessment_id')
        dry_run = options.get('dry_run', False)
        
        if assessment_id:
            assessments = Assessment.objects.filter(id=assessment_id)
            if not assessments.exists():
                self.stdout.write(
                    self.style.ERROR(f'Assessment with ID {assessment_id} not found')
                )
                return
        else:
            assessments = Assessment.objects.all()
        
        self.stdout.write(
            self.style.SUCCESS(f'Found {assessments.count()} assessments to process')
        )
        
        updated_count = 0
        error_count = 0
        
        with transaction.atomic():
            for assessment in assessments:
                try:
                    # Store old scores for comparison
                    old_scores = {
                        'overall': assessment.overall_score,
                        'strength': assessment.strength_score,
                        'mobility': assessment.mobility_score,
                        'balance': assessment.balance_score,
                        'cardio': assessment.cardio_score,
                        'injury_risk': assessment.injury_risk_score,
                    }
                    
                    # Recalculate scores
                    assessment.calculate_scores()
                    
                    # Check if scores changed
                    scores_changed = any([
                        old_scores['overall'] != assessment.overall_score,
                        old_scores['strength'] != assessment.strength_score,
                        old_scores['mobility'] != assessment.mobility_score,
                        old_scores['balance'] != assessment.balance_score,
                        old_scores['cardio'] != assessment.cardio_score,
                        old_scores['injury_risk'] != assessment.injury_risk_score,
                    ])
                    
                    if scores_changed:
                        if dry_run:
                            self.stdout.write(
                                f"Would update Assessment #{assessment.id} for {assessment.client.name}:"
                            )
                            self.stdout.write(f"  Overall: {old_scores['overall']} → {assessment.overall_score}")
                            self.stdout.write(f"  Strength: {old_scores['strength']} → {assessment.strength_score}")
                            self.stdout.write(f"  Mobility: {old_scores['mobility']} → {assessment.mobility_score}")
                            self.stdout.write(f"  Balance: {old_scores['balance']} → {assessment.balance_score}")
                            self.stdout.write(f"  Cardio: {old_scores['cardio']} → {assessment.cardio_score}")
                            self.stdout.write(f"  Injury Risk: {old_scores['injury_risk']} → {assessment.injury_risk_score}")
                        else:
                            assessment.save(update_fields=[
                                'overall_score', 'strength_score', 'mobility_score',
                                'balance_score', 'cardio_score', 'injury_risk_score', 'risk_factors'
                            ])
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f"Updated Assessment #{assessment.id} for {assessment.client.name}"
                                )
                            )
                        updated_count += 1
                    else:
                        self.stdout.write(
                            f"No changes for Assessment #{assessment.id} for {assessment.client.name}"
                        )
                        
                except Exception as e:
                    error_count += 1
                    self.stdout.write(
                        self.style.ERROR(
                            f"Error processing Assessment #{assessment.id}: {str(e)}"
                        )
                    )
            
            if dry_run:
                # Rollback the transaction in dry-run mode
                transaction.set_rollback(True)
                self.stdout.write(
                    self.style.WARNING(
                        f"\nDry run complete. Would update {updated_count} assessments."
                    )
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"\nSuccessfully updated {updated_count} assessments."
                    )
                )
                
            if error_count > 0:
                self.stdout.write(
                    self.style.ERROR(f"Encountered {error_count} errors.")
                )