from django.contrib import admin
from .models import Booking, Report, Favorite

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('id', 'client', 'provider', 'service_date', 'status', 'created_at')
    list_filter = ('status', 'service_date')
    search_fields = ('client__username', 'provider__business_name')

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('id', 'reporter', 'provider', 'is_resolved', 'created_at')
    list_filter = ('is_resolved',)
    search_fields = ('reporter__username', 'provider__business_name')

@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'provider', 'added_at')
    search_fields = ('user__username', 'provider__business_name')
