from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, ActivityLog

class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ('id', 'username', 'email', 'role', 'is_active', 'is_staff')
    list_filter = ('role', 'is_active', 'is_staff')
    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'profile_picture')}),
        ('Permissions', {'fields': ('role', 'is_active', 'is_staff', 'is_superuser')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'role')}
        ),
    )
    search_fields = ('username', 'email')
    ordering = ('id',)

admin.site.register(User, CustomUserAdmin)

@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'timestamp')
    list_filter = ('user', 'action', 'timestamp')
    ordering = ('-timestamp',)
