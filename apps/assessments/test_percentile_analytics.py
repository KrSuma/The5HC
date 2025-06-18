"""
Tests for percentile rankings and performance age calculations.
"""

import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import date, timedelta

from apps.assessments.models import Assessment, NormativeData
from apps.clients.models import Client
from apps.trainers.factories import TrainerFactory
from apps.clients.factories import ClientFactory

User = get_user_model()


class TestNormativeData(TestCase):
    """Test NormativeData model functionality"""
    
    def setUp(self):
        self.norm_data = NormativeData.objects.create(
            test_type='push_up',
            gender='M',
            age_min=30,
            age_max=39,
            percentile_10=13,
            percentile_25=17,
            percentile_50=22,
            percentile_75=30,
            percentile_90=39,
            source='ACSM Guidelines',
            year=2021,
            sample_size=5000
        )
    
    def test_get_percentile_exact_match(self):
        """Test percentile calculation for exact matches"""
        assert self.norm_data.get_percentile(13) == 10
        assert self.norm_data.get_percentile(17) == 25
        assert self.norm_data.get_percentile(22) == 50
        assert self.norm_data.get_percentile(30) == 75
        assert self.norm_data.get_percentile(39) == 90
    
    def test_get_percentile_interpolation(self):
        """Test linear interpolation between percentiles"""
        # Between 10th and 25th percentile
        score = 15  # Halfway between 13 and 17
        expected = 17.5  # Halfway between 10 and 25
        assert abs(self.norm_data.get_percentile(score) - expected) < 1
        
        # Between 50th and 75th percentile
        score = 26  # Halfway between 22 and 30
        expected = 62.5  # Halfway between 50 and 75
        assert abs(self.norm_data.get_percentile(score) - expected) < 1
    
    def test_get_percentile_extremes(self):
        """Test percentile calculation for extreme values"""
        # Below 10th percentile
        assert self.norm_data.get_percentile(5) == 10
        assert self.norm_data.get_percentile(10) == 10
        
        # Above 90th percentile
        assert self.norm_data.get_percentile(50) == 90
        assert self.norm_data.get_percentile(100) == 90
    
    def test_string_representation(self):
        """Test model string representation"""
        expected = "Push Up - 남성 (30-39)"
        assert str(self.norm_data) == expected


class TestPercentileRankings(TestCase):
    """Test assessment percentile ranking calculations"""
    
    def setUp(self):
        # Create test trainer
        self.trainer = TrainerFactory()
        
        # Create client with proper age and gender format
        self.client_obj = Client.objects.create(
            name='Test Client',
            email='client@test.com',
            phone='010-1234-5678',
            age=35,
            gender='male',
            height=175.0,
            weight=75.0,
            trainer=self.trainer
        )
        
        # Create assessment
        self.assessment = Assessment.objects.create(
            client=self.client_obj,
            trainer=self.trainer.user,
            date=timezone.now(),
            overhead_squat_score=2,
            push_up_score=3,
            push_up_reps=25,
            farmer_carry_score=4,
            toe_touch_score=2,
            shoulder_mobility_score=3,
            overall_score=65,
            strength_score=70,
            mobility_score=60,
            balance_score=55,
            cardio_score=65
        )
        
        # Create normative data
        self.create_normative_data()
    
    def create_normative_data(self):
        """Create test normative data"""
        # Push-up norms for 30-39 year old males
        NormativeData.objects.create(
            test_type='push_up',
            gender='M',
            age_min=30,
            age_max=39,
            percentile_10=13,
            percentile_25=17,
            percentile_50=22,
            percentile_75=30,
            percentile_90=39,
            source='Test Data',
            year=2023
        )
        
        # Overall score norms
        NormativeData.objects.create(
            test_type='overall',
            gender='M',
            age_min=30,
            age_max=39,
            percentile_10=42,
            percentile_25=52,
            percentile_50=62,
            percentile_75=72,
            percentile_90=82,
            source='Test Data',
            year=2023
        )
        
        # Average (gender='A') fallback data
        NormativeData.objects.create(
            test_type='strength',
            gender='A',
            age_min=30,
            age_max=39,
            percentile_10=40,
            percentile_25=50,
            percentile_50=60,
            percentile_75=70,
            percentile_90=80,
            source='Test Data',
            year=2023
        )
    
    def test_get_percentile_rankings_basic(self):
        """Test basic percentile ranking calculation"""
        rankings = self.assessment.get_percentile_rankings()
        
        # Check that rankings were calculated
        assert 'push_up' in rankings
        assert 'overall' in rankings
        assert 'strength' in rankings
        
        # Check push-up percentile (score 3 = 25 reps)
        push_up_data = rankings['push_up']
        assert push_up_data['score'] == 3
        assert push_up_data['percentile'] > 50  # 25 reps is above median of 22
        assert push_up_data['source'] == 'Test Data'
        assert push_up_data['year'] == 2023
    
    def test_get_percentile_rankings_gender_preference(self):
        """Test that gender-specific data is preferred over average"""
        # Create gender-specific strength data
        NormativeData.objects.create(
            test_type='strength',
            gender='M',
            age_min=30,
            age_max=39,
            percentile_10=45,
            percentile_25=55,
            percentile_50=65,
            percentile_75=75,
            percentile_90=85,
            source='Gender Specific',
            year=2023
        )
        
        rankings = self.assessment.get_percentile_rankings()
        
        # Should use gender-specific data, not average
        strength_data = rankings['strength']
        assert strength_data['source'] == 'Gender Specific'
        # Score 70 should be between 50th (65) and 75th (75) percentile
        assert 50 < strength_data['percentile'] < 75
    
    def test_get_percentile_rankings_no_data(self):
        """Test handling when no normative data exists"""
        # Assessment with no matching norms
        young_client = Client.objects.create(
            name='Young Client',
            email='young@test.com',
            phone='010-9999-9999',
            age=18,
            gender='male',
            height=170.0,
            weight=65.0,
            trainer=self.trainer
        )
        
        young_assessment = Assessment.objects.create(
            client=young_client,
            trainer=self.trainer.user,
            date=timezone.now(),
            push_up_score=3,
            overall_score=65
        )
        
        rankings = young_assessment.get_percentile_rankings()
        
        # Should have entries but no percentiles
        if 'push_up' in rankings:
            assert rankings['push_up']['percentile'] is None
            assert rankings['push_up']['source'] == 'No normative data available'
    
    def test_get_percentile_rankings_no_age(self):
        """Test handling when client has no age"""
        # Client without age
        ageless_client = Client.objects.create(
            name='Ageless Client',
            email='ageless@test.com',
            phone='010-0000-0000',
            gender='male',
            height=170.0,
            weight=70.0,
            age=None,  # No age
            trainer=self.trainer
        )
        
        ageless_assessment = Assessment.objects.create(
            client=ageless_client,
            trainer=self.trainer.user,
            date=timezone.now(),
            push_up_score=3
        )
        
        rankings = ageless_assessment.get_percentile_rankings()
        
        # Should return empty rankings
        assert rankings == {}


class TestPerformanceAge(TestCase):
    """Test performance age calculations"""
    
    def setUp(self):
        # Create test trainer
        self.trainer = TrainerFactory()
        
        self.client_obj = Client.objects.create(
            name='Test Client',
            email='client@test.com',
            phone='010-1234-5678',
            age=45,
            gender='male',
            height=175.0,
            weight=75.0,
            trainer=self.trainer
        )
        
        # Create assessment
        self.assessment = Assessment.objects.create(
            client=self.client_obj,
            trainer=self.trainer.user,
            date=timezone.now(),
            overall_score=62  # Median for 30-39 age group
        )
        
        # Create normative data for different age groups
        self.create_age_norms()
    
    def create_age_norms(self):
        """Create normative data for different age groups"""
        age_groups = [
            (20, 29, 45, 55, 65, 75, 85),
            (30, 39, 42, 52, 62, 72, 82),
            (40, 49, 38, 48, 58, 68, 78),
            (50, 59, 35, 45, 55, 65, 75),
            (60, 69, 30, 40, 50, 60, 70),
        ]
        
        for age_min, age_max, p10, p25, p50, p75, p90 in age_groups:
            NormativeData.objects.create(
                test_type='overall',
                gender='M',
                age_min=age_min,
                age_max=age_max,
                percentile_10=p10,
                percentile_25=p25,
                percentile_50=p50,
                percentile_75=p75,
                percentile_90=p90,
                source='Test Data',
                year=2023
            )
    
    def test_calculate_performance_age_exact_match(self):
        """Test performance age when score matches 50th percentile"""
        result = self.assessment.calculate_performance_age()
        
        assert result is not None
        assert result['chronological_age'] == 45
        # Score 62 is 50th percentile for 30-39 age group
        assert 30 <= result['performance_age'] <= 39
        assert result['age_difference'] > 5  # Performing younger
        assert '젊음' in result['interpretation']
    
    def test_calculate_performance_age_young_performance(self):
        """Test when performing much younger than actual age"""
        # High score typical of younger age group
        self.assessment.overall_score = 75  # 75th percentile for 20-29
        self.assessment.save()
        
        result = self.assessment.calculate_performance_age()
        
        assert result['performance_age'] < 30  # Should be in 20s
        assert result['age_difference'] > 15  # Much younger performance
        assert '매우 우수' in result['interpretation']
    
    def test_calculate_performance_age_old_performance(self):
        """Test when performing older than actual age"""
        # Low score typical of older age group
        self.assessment.overall_score = 45  # Between 25th-50th for 50-59
        self.assessment.save()
        
        result = self.assessment.calculate_performance_age()
        
        assert result['performance_age'] > 50  # Should be in 50s
        assert result['age_difference'] < 0  # Older performance
        assert '개선 필요' in result['interpretation']
    
    def test_calculate_performance_age_no_score(self):
        """Test handling when no overall score exists"""
        self.assessment.overall_score = None
        self.assessment.save()
        
        result = self.assessment.calculate_performance_age()
        
        assert result is None
    
    def test_interpret_age_difference(self):
        """Test age difference interpretation messages"""
        interpretations = [
            (15, "매우 우수"),
            (7, "우수"),
            (2, "양호"),
            (-3, "평균"),
            (-7, "개선 필요"),
            (-12, "즉각적 개선 필요"),
        ]
        
        for diff, expected_text in interpretations:
            interpretation = self.assessment._interpret_age_difference(diff)
            assert expected_text in interpretation


class TestManagementCommand(TestCase):
    """Test load_normative_data management command"""
    
    def test_command_creates_normative_data(self):
        """Test that management command creates normative data"""
        from django.core.management import call_command
        
        # Clear existing data
        NormativeData.objects.all().delete()
        
        # Run command
        call_command('load_normative_data', '--source=ACSM')
        
        # Check that data was created
        assert NormativeData.objects.filter(source__contains='ACSM').exists()
        assert NormativeData.objects.filter(test_type='push_up').exists()
        assert NormativeData.objects.filter(test_type='harvard_step').exists()
    
    def test_command_clear_option(self):
        """Test --clear option removes existing data"""
        # Create some data
        NormativeData.objects.create(
            test_type='test',
            gender='M',
            age_min=20,
            age_max=29,
            percentile_10=10,
            percentile_25=25,
            percentile_50=50,
            percentile_75=75,
            percentile_90=90,
            source='Old Data',
            year=2020
        )
        
        # Run command with clear
        from django.core.management import call_command
        call_command('load_normative_data', '--clear', '--source=ACSM')
        
        # Old data should be gone
        assert not NormativeData.objects.filter(source='Old Data').exists()
        # New data should exist
        assert NormativeData.objects.filter(source__contains='ACSM').exists()