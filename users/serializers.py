from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User


class SignupSerializer(serializers.ModelSerializer):

    password  = serializers.CharField(write_only=True, min_length=8)
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model  = User
        fields = ['id', 'email', 'username', 'password', 'password2', 'role']
        extra_kwargs = {
            'role': {'required': False}
        }

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate(self, data):
        """
        Object-level validation — runs after all field-level validation.
        Used when you need to compare multiple fields together.
        """
        if data['password'] != data['password2']:
            raise serializers.ValidationError({"password": "Passwords do not match."})
        return data

    def create(self, validated_data):
        validated_data.pop('password2')  # remove confirm password before saving
        password = validated_data.pop('password')

        user = User(**validated_data)
        user.set_password(password)      # hashes the password
        user.save()
        return user


class LoginSerializer(serializers.Serializer):

    email    = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        email    = data.get('email')
        password = data.get('password')

        # authenticate() checks email + password against DB
        user = authenticate(username=email, password=password)

        if not user:
            raise serializers.ValidationError("Invalid email or password.")

        if not user.is_active:
            raise serializers.ValidationError("This account has been disabled.")

        # attach user to validated_data so the view can access it
        data['user'] = user
        return data