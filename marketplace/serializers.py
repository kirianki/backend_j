from rest_framework import serializers
from rest_framework_gis.fields import GeometryField
from .models import Sector, Subcategory, ProviderProfile, PortfolioMedia, Review
from django.db.models import Avg

class SectorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sector
        fields = ['id', 'name', 'description', 'thumbnail', 'updated_at']

class SubcategorySerializer(serializers.ModelSerializer):
    sector_name = serializers.CharField(source='sector.name', read_only=True)

    class Meta:
        model = Subcategory
        fields = ['id', 'name', 'sector', 'sector_name', 'description', 'thumbnail', 'updated_at']

class PortfolioMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = PortfolioMedia
        fields = ['id', 'media_type', 'file', 'caption', 'uploaded_at']

class ProviderProfileSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    user_username = serializers.CharField(source='user.username', read_only=True)
    user_profile_picture = serializers.SerializerMethodField()
    sector = serializers.PrimaryKeyRelatedField(queryset=Sector.objects.all(), allow_null=True, required=False)
    subcategory = serializers.PrimaryKeyRelatedField(queryset=Subcategory.objects.all(), allow_null=True, required=False)
    sector_name = serializers.CharField(source='sector.name', read_only=True)
    subcategory_name = serializers.CharField(source='subcategory.name', read_only=True)
    location = GeometryField(required=False, allow_null=True)
    portfolio_media = serializers.SerializerMethodField()
    avg_rating = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()  # Keeping both for backward compatibility

    class Meta:
        model = ProviderProfile
        fields = [
            'id', 'user_id', 'user_username', 'user_profile_picture', 'business_name', 
            'address', 'location', 'sector', 'sector_name', 'subcategory', 
            'subcategory_name', 'description', 'website', 'county', 'subcounty', 
            'town', 'verification_document', 'is_verified', 'tags', 'is_featured', 
            'membership_tier', 'portfolio_media', 'updated_at', 'avg_rating', 'average_rating'
        ]
        read_only_fields = [
            'id', 'user_id', 'user_username', 'user_profile_picture', 
            'is_verified', 'verification_document', 'avg_rating', 'average_rating'
        ]

    def get_user_profile_picture(self, obj):
        if not obj.user.profile_picture:
            return None
        
        request = self.context.get('request')
        if request is not None:
            return request.build_absolute_uri(obj.user.profile_picture.url)
        return obj.user.profile_picture.url

    def get_portfolio_media(self, obj):
        from .models import PortfolioMedia
        media = obj.portfolio_media.all()
        return PortfolioMediaSerializer(media, many=True).data

    def get_avg_rating(self, obj):
        if hasattr(obj, 'avg_rating'):
            return obj.avg_rating
        return obj.average_rating

    def get_average_rating(self, obj):
        return self.get_avg_rating(obj)

class ReviewSerializer(serializers.ModelSerializer):
    provider_name = serializers.CharField(source='provider.business_name', read_only=True)
    client_username = serializers.CharField(source='client.username', read_only=True)
    provider_avg_rating = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = [
            'id', 'provider', 'provider_name', 'client', 'client_username', 
            'rating', 'comment', 'provider_response', 'created_at', 
            'is_approved', 'upvotes', 'downvotes', 'provider_avg_rating'
        ]
        read_only_fields = [
            'id', 'client', 'created_at', 'is_approved', 
            'upvotes', 'downvotes', 'provider_avg_rating'
        ]

    def get_provider_avg_rating(self, obj):
        return obj.provider.average_rating