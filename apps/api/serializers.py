"""
Serializers for The5HC API
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from apps.clients.models import Client
from apps.assessments.models import Assessment
from apps.sessions.models import SessionPackage, Session, Payment

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 
                  'is_active', 'date_joined', 'last_login']
        read_only_fields = ['id', 'date_joined', 'last_login']


class ClientSerializer(serializers.ModelSerializer):
    """Serializer for Client model"""
    age = serializers.ReadOnlyField()
    BMI = serializers.ReadOnlyField()
    bmi_category = serializers.ReadOnlyField()
    trainer_name = serializers.CharField(source='trainer.get_full_name', read_only=True)
    
    class Meta:
        model = Client
        fields = ['id', 'trainer', 'trainer_name', 'name', 'birth_date', 'age', 
                  'phone_number', 'email', 'height', 'weight', 'BMI', 'bmi_category',
                  'injury_history', 'health_notes', 'goals', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at', 'trainer']
    
    def create(self, validated_data):
        """Create client with current user as trainer"""
        validated_data['trainer'] = self.context['request'].user
        return super().create(validated_data)


class ClientListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for client listings"""
    age = serializers.ReadOnlyField()
    BMI = serializers.ReadOnlyField()
    
    class Meta:
        model = Client
        fields = ['id', 'name', 'phone_number', 'age', 'BMI', 'created_at']


class AssessmentSerializer(serializers.ModelSerializer):
    """Serializer for Assessment model"""
    client_name = serializers.CharField(source='client.name', read_only=True)
    trainer_name = serializers.CharField(source='trainer.get_full_name', read_only=True)
    
    # Computed properties
    harvard_step_test_score = serializers.ReadOnlyField()
    harvard_step_test_pfi = serializers.ReadOnlyField()
    single_leg_balance_score = serializers.ReadOnlyField()
    
    # Test variation fields with help text
    push_up_type = serializers.ChoiceField(
        choices=[('standard', '표준'), ('modified', '수정된'), ('wall', '벽')],
        default='standard',
        required=False,
        help_text="Type of push-up performed (standard/modified/wall)"
    )
    farmer_carry_percentage = serializers.FloatField(
        required=False,
        allow_null=True,
        min_value=0,
        max_value=200,
        help_text="Percentage of body weight used for farmer's carry"
    )
    test_environment = serializers.ChoiceField(
        choices=[('indoor', '실내'), ('outdoor', '실외')],
        default='indoor',
        required=False,
        help_text="Environment where tests were conducted"
    )
    temperature = serializers.FloatField(
        required=False,
        allow_null=True,
        min_value=-10,
        max_value=50,
        help_text="Ambient temperature in Celsius during testing"
    )
    
    class Meta:
        model = Assessment
        fields = ['id', 'client', 'client_name', 'trainer', 'trainer_name', 'date',
                  # FMS Tests
                  'overhead_squat_score', 'overhead_squat_notes',
                  'overhead_squat_knee_valgus', 'overhead_squat_forward_lean', 
                  'overhead_squat_heel_lift',
                  # Push-up Test
                  'push_up_reps', 'push_up_score', 'push_up_notes',
                  'push_up_type',  # Test variation field
                  # Single Leg Balance
                  'single_leg_balance_left_eyes_open', 'single_leg_balance_right_eyes_open',
                  'single_leg_balance_left_eyes_closed', 'single_leg_balance_right_eyes_closed',
                  'single_leg_balance_score', 'single_leg_balance_notes',
                  # Toe Touch Test
                  'toe_touch_distance', 'toe_touch_score', 'toe_touch_notes',
                  # Shoulder Mobility
                  'shoulder_mobility_left', 'shoulder_mobility_right', 
                  'shoulder_mobility_score', 'shoulder_mobility_notes',
                  'shoulder_mobility_pain', 'shoulder_mobility_asymmetry',
                  # Farmer's Carry
                  'farmer_carry_weight', 'farmer_carry_distance', 'farmer_carry_time',
                  'farmer_carry_score', 'farmer_carry_notes',
                  'farmer_carry_percentage',  # Test variation field
                  # Harvard Step Test
                  'harvard_step_test_hr1', 'harvard_step_test_hr2', 'harvard_step_test_hr3',
                  'harvard_step_test_score', 'harvard_step_test_pfi', 'harvard_step_test_notes',
                  # Test Environment
                  'test_environment', 'temperature',  # Test variation fields
                  # Category scores
                  'overall_score', 'strength_score', 'mobility_score', 
                  'balance_score', 'cardio_score',
                  # Risk Assessment
                  'injury_risk_score', 'risk_factors',
                  # Metadata
                  'created_at']
        read_only_fields = ['id', 'trainer', 'created_at', 'overall_score', 
                           'strength_score', 'mobility_score', 'balance_score', 
                           'cardio_score', 'injury_risk_score', 'risk_factors']
    
    def create(self, validated_data):
        """Create assessment with current user's trainer"""
        # Get the trainer associated with the current user
        from apps.trainers.models import Trainer
        trainer = Trainer.objects.get(user=self.context['request'].user)
        validated_data['trainer'] = trainer
        return super().create(validated_data)


class AssessmentListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for assessment listings"""
    client_name = serializers.CharField(source='client.name', read_only=True)
    overall_score = serializers.ReadOnlyField()
    injury_risk_score = serializers.ReadOnlyField()
    
    class Meta:
        model = Assessment
        fields = ['id', 'client', 'client_name', 'date', 'overall_score', 
                  'injury_risk_score', 'created_at']


class SessionPackageSerializer(serializers.ModelSerializer):
    """Serializer for SessionPackage model"""
    client_name = serializers.CharField(source='client.name', read_only=True)
    trainer_name = serializers.CharField(source='trainer.get_full_name', read_only=True)
    
    class Meta:
        model = SessionPackage
        fields = ['id', 'client', 'client_name', 'trainer', 'trainer_name',
                  'package_name', 'total_sessions', 'remaining_sessions',
                  'session_price', 'total_amount', 'vat_amount', 'card_fee_amount',
                  'net_amount', 'is_active', 'notes', 'created_at', 'updated_at']
        read_only_fields = ['id', 'trainer', 'vat_amount', 'card_fee_amount', 'net_amount',
                           'created_at', 'updated_at']
    
    def create(self, validated_data):
        """Create package with current user as trainer"""
        validated_data['trainer'] = self.context['request'].user
        return super().create(validated_data)


class SessionSerializer(serializers.ModelSerializer):
    """Serializer for Session model"""
    package_client_name = serializers.CharField(source='package.client.name', read_only=True)
    package_type = serializers.CharField(source='package.package_type', read_only=True)
    date = serializers.DateField(source='session_date')
    time = serializers.TimeField(source='session_time', required=False)
    duration = serializers.IntegerField(source='session_duration')
    cost = serializers.DecimalField(source='session_cost', max_digits=10, decimal_places=2)
    
    class Meta:
        model = Session
        fields = ['id', 'package', 'package_client_name', 'package_type',
                  'date', 'time', 'duration', 'cost', 'status', 'notes',
                  'created_at', 'completed_at']
        read_only_fields = ['id', 'created_at', 'completed_at']


class PaymentSerializer(serializers.ModelSerializer):
    """Serializer for Payment model"""
    client_name = serializers.CharField(source='client.name', read_only=True)
    package_type = serializers.CharField(source='package.package_type', read_only=True, allow_null=True)
    
    class Meta:
        model = Payment
        fields = ['id', 'client', 'client_name', 'package', 'package_type',
                  'amount', 'payment_method', 'payment_date', 'description',
                  'gross_amount', 'vat_amount', 'card_fee_amount', 'net_amount',
                  'created_at']
        read_only_fields = ['id', 'created_at', 'gross_amount', 'vat_amount', 
                           'card_fee_amount', 'net_amount']


# Authentication Serializers
class LoginSerializer(serializers.Serializer):
    """Serializer for user login"""
    email_or_username = serializers.CharField(max_length=150)
    password = serializers.CharField(style={'input_type': 'password'})


class TokenRefreshSerializer(serializers.Serializer):
    """Serializer for token refresh"""
    refresh = serializers.CharField()


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for changing password"""
    old_password = serializers.CharField(style={'input_type': 'password'})
    new_password = serializers.CharField(style={'input_type': 'password'})
    confirm_password = serializers.CharField(style={'input_type': 'password'})
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError("새 비밀번호가 일치하지 않습니다.")
        return attrs