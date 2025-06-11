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
    total_score = serializers.ReadOnlyField()
    fitness_score = serializers.ReadOnlyField()
    posture_score = serializers.ReadOnlyField()
    
    class Meta:
        model = Assessment
        fields = ['id', 'client', 'client_name', 'date', 
                  # Category scores
                  'endurance', 'strength', 'flexibility', 'balance', 'coordination',
                  'agility', 'power', 'reaction_time', 'cardiovascular', 'core_stability',
                  # Posture assessment
                  'posture_score', 'head_forward', 'shoulder_internal_rotation',
                  'shoulder_elevation', 'trunk_flexion', 'pelvic_anterior_tilt',
                  'knee_hyperextension', 'foot_arch', 'c_curve', 's_curve',
                  # Movement tests
                  'squat_heel_raise', 'squat_knee_valgus', 'lunge_knee_valgus',
                  'shoulder_flexion_rom', 'shoulder_extension_rom', 'trunk_rotation_rom',
                  'hip_flexion_rom',
                  # Calculated scores
                  'fitness_score', 'total_score',
                  # Metadata
                  'notes', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class AssessmentListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for assessment listings"""
    client_name = serializers.CharField(source='client.name', read_only=True)
    overall_score = serializers.ReadOnlyField()
    
    class Meta:
        model = Assessment
        fields = ['id', 'client', 'client_name', 'date', 'overall_score', 'created_at']


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