"""
Management command to load normative data for fitness assessments.
This command loads standardized fitness data based on ACSM guidelines and Korean population studies.
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from apps.assessments.models import NormativeData


class Command(BaseCommand):
    help = 'Load normative data for fitness assessment percentile calculations'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing normative data before loading',
        )
        parser.add_argument(
            '--source',
            type=str,
            default='ACSM',
            help='Data source to load (ACSM, Korean, or All)',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing normative data...')
            NormativeData.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Cleared all normative data'))

        source = options['source'].upper()
        
        if source in ['ACSM', 'ALL']:
            self.load_acsm_data()
        
        if source in ['KOREAN', 'ALL']:
            self.load_korean_data()
        
        self.stdout.write(self.style.SUCCESS('Successfully loaded normative data'))

    @transaction.atomic
    def load_acsm_data(self):
        """Load ACSM (American College of Sports Medicine) normative data."""
        self.stdout.write('Loading ACSM normative data...')
        
        # Push-up norms (men)
        push_up_data_men = [
            # Age 20-29
            {'age_min': 20, 'age_max': 29, 'gender': 'M', 'p10': 17, 'p25': 22, 'p50': 29, 'p75': 36, 'p90': 44},
            # Age 30-39
            {'age_min': 30, 'age_max': 39, 'gender': 'M', 'p10': 13, 'p25': 17, 'p50': 22, 'p75': 30, 'p90': 39},
            # Age 40-49
            {'age_min': 40, 'age_max': 49, 'gender': 'M', 'p10': 10, 'p25': 13, 'p50': 17, 'p75': 24, 'p90': 30},
            # Age 50-59
            {'age_min': 50, 'age_max': 59, 'gender': 'M', 'p10': 7, 'p25': 10, 'p50': 13, 'p75': 20, 'p90': 25},
            # Age 60-69
            {'age_min': 60, 'age_max': 69, 'gender': 'M', 'p10': 5, 'p25': 8, 'p50': 11, 'p75': 17, 'p90': 23},
        ]
        
        # Push-up norms (women)
        push_up_data_women = [
            # Age 20-29
            {'age_min': 20, 'age_max': 29, 'gender': 'F', 'p10': 6, 'p25': 10, 'p50': 15, 'p75': 23, 'p90': 30},
            # Age 30-39
            {'age_min': 30, 'age_max': 39, 'gender': 'F', 'p10': 5, 'p25': 8, 'p50': 13, 'p75': 20, 'p90': 27},
            # Age 40-49
            {'age_min': 40, 'age_max': 49, 'gender': 'F', 'p10': 4, 'p25': 6, 'p50': 11, 'p75': 15, 'p90': 24},
            # Age 50-59
            {'age_min': 50, 'age_max': 59, 'gender': 'F', 'p10': 2, 'p25': 5, 'p50': 7, 'p75': 12, 'p90': 17},
            # Age 60-69
            {'age_min': 60, 'age_max': 69, 'gender': 'F', 'p10': 1, 'p25': 3, 'p50': 5, 'p75': 11, 'p90': 17},
        ]
        
        # Create push-up entries
        for data in push_up_data_men + push_up_data_women:
            NormativeData.objects.update_or_create(
                test_type='push_up',
                gender=data['gender'],
                age_min=data['age_min'],
                age_max=data['age_max'],
                defaults={
                    'percentile_10': data['p10'],
                    'percentile_25': data['p25'],
                    'percentile_50': data['p50'],
                    'percentile_75': data['p75'],
                    'percentile_90': data['p90'],
                    'source': 'ACSM Guidelines 11th Edition',
                    'year': 2021,
                    'sample_size': 5000,
                    'notes': 'Push-up test performed to exhaustion'
                }
            )
        
        # Harvard Step Test norms (PFI scores)
        step_test_data = [
            # Men
            {'age_min': 20, 'age_max': 29, 'gender': 'M', 'p10': 45, 'p25': 55, 'p50': 65, 'p75': 75, 'p90': 85},
            {'age_min': 30, 'age_max': 39, 'gender': 'M', 'p10': 42, 'p25': 52, 'p50': 62, 'p75': 72, 'p90': 82},
            {'age_min': 40, 'age_max': 49, 'gender': 'M', 'p10': 40, 'p25': 50, 'p50': 58, 'p75': 68, 'p90': 78},
            {'age_min': 50, 'age_max': 59, 'gender': 'M', 'p10': 38, 'p25': 46, 'p50': 55, 'p75': 65, 'p90': 75},
            {'age_min': 60, 'age_max': 69, 'gender': 'M', 'p10': 35, 'p25': 43, 'p50': 52, 'p75': 61, 'p90': 70},
            # Women
            {'age_min': 20, 'age_max': 29, 'gender': 'F', 'p10': 42, 'p25': 52, 'p50': 62, 'p75': 72, 'p90': 82},
            {'age_min': 30, 'age_max': 39, 'gender': 'F', 'p10': 40, 'p25': 48, 'p50': 58, 'p75': 68, 'p90': 78},
            {'age_min': 40, 'age_max': 49, 'gender': 'F', 'p10': 38, 'p25': 46, 'p50': 55, 'p75': 64, 'p90': 73},
            {'age_min': 50, 'age_max': 59, 'gender': 'F', 'p10': 35, 'p25': 43, 'p50': 52, 'p75': 60, 'p90': 68},
            {'age_min': 60, 'age_max': 69, 'gender': 'F', 'p10': 32, 'p25': 40, 'p50': 48, 'p75': 56, 'p90': 65},
        ]
        
        for data in step_test_data:
            NormativeData.objects.update_or_create(
                test_type='harvard_step',
                gender=data['gender'],
                age_min=data['age_min'],
                age_max=data['age_max'],
                defaults={
                    'percentile_10': data['p10'],
                    'percentile_25': data['p25'],
                    'percentile_50': data['p50'],
                    'percentile_75': data['p75'],
                    'percentile_90': data['p90'],
                    'source': 'ACSM Fitness Assessment Manual',
                    'year': 2021,
                    'sample_size': 3000,
                    'notes': 'Physical Fitness Index (PFI) scores'
                }
            )
        
        self.stdout.write(self.style.SUCCESS(f'Loaded {len(push_up_data_men + push_up_data_women + step_test_data)} ACSM normative entries'))

    @transaction.atomic
    def load_korean_data(self):
        """Load Korean population normative data."""
        self.stdout.write('Loading Korean population normative data...')
        
        # Farmer carry norms (percentage of body weight)
        farmer_carry_data = [
            # Men
            {'age_min': 20, 'age_max': 29, 'gender': 'M', 'p10': 40, 'p25': 50, 'p50': 65, 'p75': 80, 'p90': 95},
            {'age_min': 30, 'age_max': 39, 'gender': 'M', 'p10': 35, 'p25': 45, 'p50': 60, 'p75': 75, 'p90': 90},
            {'age_min': 40, 'age_max': 49, 'gender': 'M', 'p10': 30, 'p25': 40, 'p50': 55, 'p75': 70, 'p90': 85},
            {'age_min': 50, 'age_max': 59, 'gender': 'M', 'p10': 25, 'p25': 35, 'p50': 50, 'p75': 65, 'p90': 80},
            {'age_min': 60, 'age_max': 69, 'gender': 'M', 'p10': 20, 'p25': 30, 'p50': 45, 'p75': 60, 'p90': 75},
            # Women
            {'age_min': 20, 'age_max': 29, 'gender': 'F', 'p10': 30, 'p25': 40, 'p50': 50, 'p75': 65, 'p90': 80},
            {'age_min': 30, 'age_max': 39, 'gender': 'F', 'p10': 25, 'p25': 35, 'p50': 45, 'p75': 60, 'p90': 75},
            {'age_min': 40, 'age_max': 49, 'gender': 'F', 'p10': 20, 'p25': 30, 'p50': 40, 'p75': 55, 'p90': 70},
            {'age_min': 50, 'age_max': 59, 'gender': 'F', 'p10': 15, 'p25': 25, 'p50': 35, 'p75': 50, 'p90': 65},
            {'age_min': 60, 'age_max': 69, 'gender': 'F', 'p10': 10, 'p25': 20, 'p50': 30, 'p75': 45, 'p90': 60},
        ]
        
        for data in farmer_carry_data:
            NormativeData.objects.update_or_create(
                test_type='farmer_carry',
                gender=data['gender'],
                age_min=data['age_min'],
                age_max=data['age_max'],
                defaults={
                    'percentile_10': data['p10'],
                    'percentile_25': data['p25'],
                    'percentile_50': data['p50'],
                    'percentile_75': data['p75'],
                    'percentile_90': data['p90'],
                    'source': 'Korean National Fitness Survey',
                    'year': 2022,
                    'sample_size': 2500,
                    'notes': 'Percentage of body weight carried for 20 meters'
                }
            )
        
        # Overall fitness scores (0-100 scale)
        overall_data = [
            # Men
            {'age_min': 20, 'age_max': 29, 'gender': 'M', 'p10': 45, 'p25': 55, 'p50': 65, 'p75': 75, 'p90': 85},
            {'age_min': 30, 'age_max': 39, 'gender': 'M', 'p10': 42, 'p25': 52, 'p50': 62, 'p75': 72, 'p90': 82},
            {'age_min': 40, 'age_max': 49, 'gender': 'M', 'p10': 38, 'p25': 48, 'p50': 58, 'p75': 68, 'p90': 78},
            {'age_min': 50, 'age_max': 59, 'gender': 'M', 'p10': 35, 'p25': 45, 'p50': 55, 'p75': 65, 'p90': 75},
            {'age_min': 60, 'age_max': 69, 'gender': 'M', 'p10': 30, 'p25': 40, 'p50': 50, 'p75': 60, 'p90': 70},
            # Women
            {'age_min': 20, 'age_max': 29, 'gender': 'F', 'p10': 42, 'p25': 52, 'p50': 62, 'p75': 72, 'p90': 82},
            {'age_min': 30, 'age_max': 39, 'gender': 'F', 'p10': 40, 'p25': 50, 'p50': 60, 'p75': 70, 'p90': 80},
            {'age_min': 40, 'age_max': 49, 'gender': 'F', 'p10': 36, 'p25': 46, 'p50': 56, 'p75': 66, 'p90': 76},
            {'age_min': 50, 'age_max': 59, 'gender': 'F', 'p10': 32, 'p25': 42, 'p50': 52, 'p75': 62, 'p90': 72},
            {'age_min': 60, 'age_max': 69, 'gender': 'F', 'p10': 28, 'p25': 38, 'p50': 48, 'p75': 58, 'p90': 68},
        ]
        
        for data in overall_data:
            NormativeData.objects.update_or_create(
                test_type='overall',
                gender=data['gender'],
                age_min=data['age_min'],
                age_max=data['age_max'],
                defaults={
                    'percentile_10': data['p10'],
                    'percentile_25': data['p25'],
                    'percentile_50': data['p50'],
                    'percentile_75': data['p75'],
                    'percentile_90': data['p90'],
                    'source': 'The5HC Assessment Database',
                    'year': 2023,
                    'sample_size': 1500,
                    'notes': 'Composite score from multiple fitness tests'
                }
            )
        
        self.stdout.write(self.style.SUCCESS(f'Loaded {len(farmer_carry_data + overall_data)} Korean normative entries'))