
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User
from rest_framework import serializers
from django.contrib.auth import get_user_model


class AdminLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")

        # Hardcoded Admin Credentials
        ADMIN_EMAIL = "jinz@gmail.com"
        ADMIN_PASSWORD = "Jinz@123"

        # Validate credentials
        if email.strip() != ADMIN_EMAIL or password.strip() != ADMIN_PASSWORD:
            raise serializers.ValidationError("Invalid email or password", code="authorization")

        # Check if the admin user exists
        try:
            admin_user = User.objects.get(email=ADMIN_EMAIL, username="admin")
        except User.DoesNotExist:
            raise serializers.ValidationError("Admin user does not exist", code="authorization")

        # Generate or retrieve token
        token, _ = Token.objects.get_or_create(user=admin_user)

        return {
            "token": token.key,
            "user_id": admin_user.id,
            "email": admin_user.email,
            "is_admin": True,
            "success": True
        }



User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password', 'first_name',
                  'last_name', 'role','phone_number','address','created_at')
        read_only_fields = ('id',)

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = User(**validated_data)
        if password:
            user.set_password(password)
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if password:
            instance.set_password(password)

        instance.save()
        return instance


