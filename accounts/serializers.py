from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import User

class RegisterSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)
    role = serializers.ChoiceField(
        choices=[(role.value, role.label) for role in User.Role 
                 if role.value in [User.Role.SERVICE_PROVIDER, User.Role.CLIENT]]
    )

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password', 'password2', 'role', 'first_name', 'last_name')

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Passwords do not match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

class UserSerializer(serializers.ModelSerializer):
    role_display = serializers.CharField(source="get_role_display", read_only=True)
    profile_picture = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'role', 'role_display', 'first_name', 'last_name', 'profile_picture')

    def get_profile_picture(self, obj):
        if not obj.profile_picture:
            return None
        
        # Handle case where request might not be in context
        request = self.context.get('request')
        if request is not None:
            return request.build_absolute_uri(obj.profile_picture.url)
        return obj.profile_picture.url  # Fallback to relative URL
    
# Updated serializer for profile update to allow email and role changes.
class ProfileUpdateSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=False)
    role = serializers.ChoiceField(
        choices=[(User.Role.CLIENT, "Client"), (User.Role.SERVICE_PROVIDER, "Service Provider")],
        required=False
    )
    profile_picture = serializers.ImageField(required=False)

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'profile_picture', 'email', 'role')

    def validate_email(self, value):
        user = self.instance
        if user.email != value and User.objects.filter(email=value).exists():
            raise serializers.ValidationError("This email is already in use.")
        return value

    def validate_role(self, value):
        if value not in [User.Role.CLIENT, User.Role.SERVICE_PROVIDER]:
            raise serializers.ValidationError("Role can only be changed to 'client' or 'service_provider'.")
        return value