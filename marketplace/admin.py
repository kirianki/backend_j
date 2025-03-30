from django.contrib import admin
from .models import Sector, Subcategory, ProviderProfile, PortfolioMedia, Review

@admin.register(Sector)
class SectorAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'updated_at')
    search_fields = ('name',)

@admin.register(Subcategory)
class SubcategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'sector', 'updated_at')
    search_fields = ('name',)
    list_filter = ('sector',)

@admin.register(ProviderProfile)
class ProviderProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'business_name', 'user', 'sector', 'subcategory', 'is_verified', 'is_featured')
    search_fields = ('business_name', 'user__username')
    list_filter = ('sector', 'subcategory', 'is_verified', 'is_featured')

@admin.register(PortfolioMedia)
class PortfolioMediaAdmin(admin.ModelAdmin):
    list_display = ('id', 'provider', 'media_type', 'uploaded_at')
    list_filter = ('media_type',)

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('id', 'provider', 'client', 'rating', 'created_at', 'is_approved')
    list_filter = ('rating', 'is_approved')
    search_fields = ('provider__business_name', 'client__username')