from rest_framework import serializers
from ..models import User, Client
from apps.restaurants.models import Restaurant
from django.contrib.auth.password_validation import validate_password


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True, required=True)
    restaurant = serializers.PrimaryKeyRelatedField(
        queryset=Restaurant.objects.filter(status=True),
        required=False,  
        allow_null=True 
    )
    
    class Meta:
        model = User
        fields = ('username', 'password', 'confirm_password', 'email', 'role', 'first_name', 'last_name', 'restaurant')
    
    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords must match. Please try again.")
        return data
    
    def create(self, validated_data):
        validated_data.pop('confirm_password')

        restaurant = validated_data.pop('restaurant', None)

        user = User.objects.create(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            role=validated_data.get('role', ''),
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            restaurant=restaurant
        )
        user.set_password(validated_data['password'])
        user.save()
        return user
    

class PasswordChangeSerializer(serializers.Serializer):
    current_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])

    def validate_current_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect.")
        return value

    def update(self, instance, validated_data):
        instance.set_password(validated_data['new_password'])
        instance.save()
        return instance
    

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'role']


class ClientSerializer(serializers.ModelSerializer):
    phone = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = Client
        fields = ['id', 'name', 'email', 'phone']
        read_only_fields = ['id']

    def validate_email(self, value):
        if Client.objects.filter(email=value).exists():
            raise serializers.ValidationError("This email is already registered.")
        return value
    

class BulkClientUploadSerializer(serializers.Serializer):
    file = serializers.FileField()