"""
Management command to load test standards into the database.
This command populates the TestStandard model with default scoring thresholds.
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from apps.assessments.models import TestStandard


class Command(BaseCommand):
    help = 'Load default test standards into the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing standards before loading new ones',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be loaded without actually saving to database',
        )

    def handle(self, *args, **options):
        """Load test standards into the database."""
        
        if options['dry_run']:
            self.stdout.write(
                self.style.WARNING('DRY RUN - No data will be saved to database')
            )
        
        if options['clear'] and not options['dry_run']:
            self.stdout.write('Clearing existing test standards...')
            TestStandard.objects.all().delete()
            self.stdout.write(
                self.style.SUCCESS('Cleared existing test standards')
            )
        
        # Define default test standards
        standards_data = self._get_default_standards()
        
        created_count = 0
        updated_count = 0
        
        try:
            with transaction.atomic():
                for standard_data in standards_data:
                    if options['dry_run']:
                        self.stdout.write(f"Would create: {standard_data['name']}")
                        created_count += 1
                        continue
                    
                    # Check if standard already exists
                    existing = TestStandard.objects.filter(
                        test_type=standard_data['test_type'],
                        gender=standard_data['gender'],
                        age_min=standard_data['age_min'],
                        age_max=standard_data['age_max'],
                        variation_type=standard_data.get('variation_type'),
                        conditions=standard_data.get('conditions')
                    ).first()
                    
                    if existing:
                        # Update existing standard
                        for key, value in standard_data.items():
                            setattr(existing, key, value)
                        existing.save()
                        updated_count += 1
                        self.stdout.write(f"Updated: {existing.name}")
                    else:
                        # Create new standard
                        TestStandard.objects.create(**standard_data)
                        created_count += 1
                        self.stdout.write(f"Created: {standard_data['name']}")
                
                if not options['dry_run']:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Successfully loaded {created_count} new standards '
                            f'and updated {updated_count} existing standards'
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Would create {created_count} standards'
                        )
                    )
                    
        except Exception as e:
            raise CommandError(f'Error loading test standards: {e}')

    def _get_default_standards(self):
        """
        Return list of default test standards based on ACSM guidelines
        and Korean fitness standards.
        """
        standards = []
        
        # Push-up standards for males
        push_up_male_standards = [
            # Age 18-29
            {
                'test_type': 'push_up',
                'gender': 'M',
                'age_min': 18,
                'age_max': 29,
                'metric_type': 'repetitions',
                'excellent_threshold': 36,
                'good_threshold': 29,
                'average_threshold': 22,
                'needs_improvement_threshold': 0,
                'variation_type': 'standard',
                'name': '성인 남성 푸시업 기준 (18-29세)',
                'description': 'ACSM 가이드라인 기반 성인 남성 푸시업 평가 기준',
                'source': 'ACSM Guidelines 11th Edition',
                'year': 2022
            },
            # Age 30-39
            {
                'test_type': 'push_up',
                'gender': 'M',
                'age_min': 30,
                'age_max': 39,
                'metric_type': 'repetitions',
                'excellent_threshold': 30,
                'good_threshold': 24,
                'average_threshold': 17,
                'needs_improvement_threshold': 0,
                'variation_type': 'standard',
                'name': '성인 남성 푸시업 기준 (30-39세)',
                'description': 'ACSM 가이드라인 기반 성인 남성 푸시업 평가 기준',
                'source': 'ACSM Guidelines 11th Edition',
                'year': 2022
            },
            # Age 40-49
            {
                'test_type': 'push_up',
                'gender': 'M',
                'age_min': 40,
                'age_max': 49,
                'metric_type': 'repetitions',
                'excellent_threshold': 25,
                'good_threshold': 20,
                'average_threshold': 13,
                'needs_improvement_threshold': 0,
                'variation_type': 'standard',
                'name': '성인 남성 푸시업 기준 (40-49세)',
                'description': 'ACSM 가이드라인 기반 성인 남성 푸시업 평가 기준',
                'source': 'ACSM Guidelines 11th Edition',
                'year': 2022
            },
            # Age 50-59
            {
                'test_type': 'push_up',
                'gender': 'M',
                'age_min': 50,
                'age_max': 59,
                'metric_type': 'repetitions',
                'excellent_threshold': 21,
                'good_threshold': 16,
                'average_threshold': 10,
                'needs_improvement_threshold': 0,
                'variation_type': 'standard',
                'name': '성인 남성 푸시업 기준 (50-59세)',
                'description': 'ACSM 가이드라인 기반 성인 남성 푸시업 평가 기준',
                'source': 'ACSM Guidelines 11th Edition',
                'year': 2022
            },
            # Age 60+
            {
                'test_type': 'push_up',
                'gender': 'M',
                'age_min': 60,
                'age_max': 120,
                'metric_type': 'repetitions',
                'excellent_threshold': 18,
                'good_threshold': 12,
                'average_threshold': 8,
                'needs_improvement_threshold': 0,
                'variation_type': 'standard',
                'name': '성인 남성 푸시업 기준 (60세 이상)',
                'description': 'ACSM 가이드라인 기반 성인 남성 푸시업 평가 기준',
                'source': 'ACSM Guidelines 11th Edition',
                'year': 2022
            }
        ]
        
        # Push-up standards for females
        push_up_female_standards = [
            # Age 18-29
            {
                'test_type': 'push_up',
                'gender': 'F',
                'age_min': 18,
                'age_max': 29,
                'metric_type': 'repetitions',
                'excellent_threshold': 30,
                'good_threshold': 21,
                'average_threshold': 15,
                'needs_improvement_threshold': 0,
                'variation_type': 'standard',
                'name': '성인 여성 푸시업 기준 (18-29세)',
                'description': 'ACSM 가이드라인 기반 성인 여성 푸시업 평가 기준',
                'source': 'ACSM Guidelines 11th Edition',
                'year': 2022
            },
            # Age 30-39
            {
                'test_type': 'push_up',
                'gender': 'F',
                'age_min': 30,
                'age_max': 39,
                'metric_type': 'repetitions',
                'excellent_threshold': 27,
                'good_threshold': 20,
                'average_threshold': 13,
                'needs_improvement_threshold': 0,
                'variation_type': 'standard',
                'name': '성인 여성 푸시업 기준 (30-39세)',
                'description': 'ACSM 가이드라인 기반 성인 여성 푸시업 평가 기준',
                'source': 'ACSM Guidelines 11th Edition',
                'year': 2022
            },
            # Age 40-49
            {
                'test_type': 'push_up',
                'gender': 'F',
                'age_min': 40,
                'age_max': 49,
                'metric_type': 'repetitions',
                'excellent_threshold': 24,
                'good_threshold': 15,
                'average_threshold': 11,
                'needs_improvement_threshold': 0,
                'variation_type': 'standard',
                'name': '성인 여성 푸시업 기준 (40-49세)',
                'description': 'ACSM 가이드라인 기반 성인 여성 푸시업 평가 기준',
                'source': 'ACSM Guidelines 11th Edition',
                'year': 2022
            },
            # Age 50-59
            {
                'test_type': 'push_up',
                'gender': 'F',
                'age_min': 50,
                'age_max': 59,
                'metric_type': 'repetitions',
                'excellent_threshold': 21,
                'good_threshold': 13,
                'average_threshold': 9,
                'needs_improvement_threshold': 0,
                'variation_type': 'standard',
                'name': '성인 여성 푸시업 기준 (50-59세)',
                'description': 'ACSM 가이드라인 기반 성인 여성 푸시업 평가 기준',
                'source': 'ACSM Guidelines 11th Edition',
                'year': 2022
            },
            # Age 60+
            {
                'test_type': 'push_up',
                'gender': 'F',
                'age_min': 60,
                'age_max': 120,
                'metric_type': 'repetitions',
                'excellent_threshold': 17,
                'good_threshold': 12,
                'average_threshold': 8,
                'needs_improvement_threshold': 0,
                'variation_type': 'standard',
                'name': '성인 여성 푸시업 기준 (60세 이상)',
                'description': 'ACSM 가이드라인 기반 성인 여성 푸시업 평가 기준',
                'source': 'ACSM Guidelines 11th Edition',
                'year': 2022
            }
        ]
        
        # Modified push-up standards (70% of standard)
        modified_push_up_standards = []
        for standard in push_up_male_standards + push_up_female_standards:
            modified_standard = standard.copy()
            modified_standard['variation_type'] = 'modified'
            modified_standard['name'] = modified_standard['name'].replace('푸시업', '수정된 푸시업')
            modified_standard['excellent_threshold'] = round(standard['excellent_threshold'] * 0.7)
            modified_standard['good_threshold'] = round(standard['good_threshold'] * 0.7)
            modified_standard['average_threshold'] = round(standard['average_threshold'] * 0.7)
            modified_standard['description'] = modified_standard['description'].replace('푸시업', '수정된 푸시업 (무릎)')
            modified_push_up_standards.append(modified_standard)
        
        # Wall push-up standards (40% of standard)
        wall_push_up_standards = []
        for standard in push_up_male_standards + push_up_female_standards:
            wall_standard = standard.copy()
            wall_standard['variation_type'] = 'wall'
            wall_standard['name'] = wall_standard['name'].replace('푸시업', '벽 푸시업')
            wall_standard['excellent_threshold'] = round(standard['excellent_threshold'] * 0.4)
            wall_standard['good_threshold'] = round(standard['good_threshold'] * 0.4)
            wall_standard['average_threshold'] = round(standard['average_threshold'] * 0.4)
            wall_standard['description'] = wall_standard['description'].replace('푸시업', '벽 푸시업')
            wall_push_up_standards.append(wall_standard)
        
        # Single leg balance standards
        balance_standards = [
            # Eyes open - general standard
            {
                'test_type': 'balance',
                'gender': 'A',
                'age_min': 18,
                'age_max': 120,
                'metric_type': 'time',
                'excellent_threshold': 45,
                'good_threshold': 30,
                'average_threshold': 15,
                'needs_improvement_threshold': 0,
                'conditions': 'eyes_open',
                'name': '외다리 균형 기준 (눈뜨고)',
                'description': '외다리 서기 균형 평가 기준 (눈을 뜬 상태)',
                'source': 'ACSM Guidelines',
                'year': 2022
            },
            # Eyes closed - general standard
            {
                'test_type': 'balance',
                'gender': 'A',
                'age_min': 18,
                'age_max': 120,
                'metric_type': 'time',
                'excellent_threshold': 30,
                'good_threshold': 20,
                'average_threshold': 10,
                'needs_improvement_threshold': 0,
                'conditions': 'eyes_closed',
                'name': '외다리 균형 기준 (눈감고)',
                'description': '외다리 서기 균형 평가 기준 (눈을 감은 상태)',
                'source': 'ACSM Guidelines',
                'year': 2022
            }
        ]
        
        # Farmer's carry standards (by gender and time)
        farmers_carry_standards = [
            # Male standards
            {
                'test_type': 'farmer_carry',
                'gender': 'M',
                'age_min': 18,
                'age_max': 120,
                'metric_type': 'time',
                'excellent_threshold': 60,  # Can carry for 60+ seconds
                'good_threshold': 45,
                'average_threshold': 30,
                'needs_improvement_threshold': 0,
                'name': '남성 파머스 캐리 기준 (시간)',
                'description': '체중 100% 무게로 파머스 캐리 지속 시간 평가',
                'source': 'Functional Movement Standards',
                'year': 2022
            },
            # Female standards
            {
                'test_type': 'farmer_carry',
                'gender': 'F',
                'age_min': 18,
                'age_max': 120,
                'metric_type': 'time',
                'excellent_threshold': 45,
                'good_threshold': 30,
                'average_threshold': 20,
                'needs_improvement_threshold': 0,
                'name': '여성 파머스 캐리 기준 (시간)',
                'description': '체중 100% 무게로 파머스 캐리 지속 시간 평가',
                'source': 'Functional Movement Standards',
                'year': 2022
            }
        ]
        
        # Harvard Step Test standards (PFI - Physical Fitness Index)
        step_test_standards = [
            {
                'test_type': 'step_test',
                'gender': 'A',
                'age_min': 18,
                'age_max': 120,
                'metric_type': 'pfi',
                'excellent_threshold': 90,
                'good_threshold': 80,
                'average_threshold': 65,
                'needs_improvement_threshold': 0,
                'name': '하버드 스텝 테스트 기준 (PFI)',
                'description': 'Physical Fitness Index 기반 심폐지구력 평가',
                'source': 'Harvard Step Test Protocol',
                'year': 2022
            }
        ]
        
        # Overhead squat standards (scored 0-3)
        overhead_squat_standards = [
            {
                'test_type': 'overhead_squat',
                'gender': 'A',
                'age_min': 18,
                'age_max': 120,
                'metric_type': 'score',
                'excellent_threshold': 3,
                'good_threshold': 2,
                'average_threshold': 1,
                'needs_improvement_threshold': 0,
                'name': '오버헤드 스쿼트 기준',
                'description': 'FMS 기반 동작 품질 평가 (0-3점)',
                'source': 'Functional Movement Screen',
                'year': 2022
            }
        ]
        
        # Toe touch standards (distance in cm, use inverted scale for flexibility)
        # Note: We'll handle the reverse scoring in the scoring logic
        toe_touch_standards = [
            {
                'test_type': 'toe_touch',
                'gender': 'A',
                'age_min': 18,
                'age_max': 120,
                'metric_type': 'distance',
                'excellent_threshold': 5,    # Can reach beyond toes
                'good_threshold': 0,         # Can touch toes
                'average_threshold': -5,     # Within 5cm of toes
                'needs_improvement_threshold': -20,  # More than 5cm from toes
                'name': '발끝 터치 기준',
                'description': '앉아서 발끝 터치 유연성 평가 (cm) - 높은 값이 좋음',
                'source': 'ACSM Flexibility Guidelines',
                'year': 2022
            }
        ]
        
        # Shoulder mobility standards (distance in cm, use inverted scale)
        # Note: We'll handle the reverse scoring in the scoring logic
        shoulder_mobility_standards = [
            {
                'test_type': 'shoulder_mobility',
                'gender': 'A',
                'age_min': 18,
                'age_max': 120,
                'metric_type': 'distance',
                'excellent_threshold': 15,   # Good mobility (reverse: 0cm actual)
                'good_threshold': 10,        # Moderate mobility (reverse: 5cm actual)
                'average_threshold': 5,      # Poor mobility (reverse: 10cm actual)
                'needs_improvement_threshold': 0,  # Very poor mobility (reverse: 15cm+ actual)
                'name': '어깨 가동성 기준',
                'description': '어깨 뒤쪽 가동성 평가 (역순 점수) - 높은 값이 좋음',
                'source': 'FMS Shoulder Mobility Test',
                'year': 2022
            }
        ]
        
        # Combine all standards
        standards.extend(push_up_male_standards)
        standards.extend(push_up_female_standards)
        standards.extend(modified_push_up_standards)
        standards.extend(wall_push_up_standards)
        standards.extend(balance_standards)
        standards.extend(farmers_carry_standards)
        standards.extend(step_test_standards)
        standards.extend(overhead_squat_standards)
        standards.extend(toe_touch_standards)
        standards.extend(shoulder_mobility_standards)
        
        # Set default values for optional fields
        for standard in standards:
            if 'variation_type' not in standard:
                standard['variation_type'] = None
            if 'conditions' not in standard:
                standard['conditions'] = None
            if 'is_active' not in standard:
                standard['is_active'] = True
        
        return standards