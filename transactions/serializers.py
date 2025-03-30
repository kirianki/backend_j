from rest_framework import serializers
from .models import Booking, Report, Favorite
from marketplace.models import ProviderProfile  # Added import

class ProviderProfileSerializer(serializers.ModelSerializer):  # New serializer
    class Meta:
        model = ProviderProfile
        fields = ['id', 'business_name', 'user']  # Customize fields as needed

class BookingSerializer(serializers.ModelSerializer):
    client = serializers.HiddenField(default=serializers.CurrentUserDefault())
    provider_id = serializers.PrimaryKeyRelatedField(
        queryset=ProviderProfile.objects.all(), 
        source='provider',
        write_only=True
    )
    provider = ProviderProfileSerializer(read_only=True)  # For responses

    class Meta:
        model = Booking
        fields = ['id', 'client', 'provider', 'provider_id', 'service_date', 'status', 'created_at']
        read_only_fields = ['status', 'client', 'created_at', 'provider']       
class ReportSerializer(serializers.ModelSerializer):
    reporter = serializers.HiddenField(default=serializers.CurrentUserDefault())
    
    class Meta:
        model = Report
        fields = ['id', 'reporter', 'provider', 'description', 'is_resolved', 'created_at']
        read_only_fields = ['is_resolved']

class FavoriteSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    
    class Meta:
        model = Favorite
        fields = ['id', 'user', 'provider', 'added_at']
