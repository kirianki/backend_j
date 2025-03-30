from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView
from .views import RegisterView, UserProfileView, LogoutView, CustomTokenObtainPairView, SpecificUserProfileView

urlpatterns = [
    path('auth/', include([
        path('register/', RegisterView.as_view(), name='auth_register'),
        path('token/', CustomTokenObtainPairView.as_view(), name='auth_token'),
        path('token/refresh/', TokenRefreshView.as_view(), name='auth_token_refresh'),
        path('logout/', LogoutView.as_view(), name='auth_logout'),
    ])),
    path('profile/', UserProfileView.as_view(), name='profile'),
    path('profile/<int:user_id>/', SpecificUserProfileView.as_view(), name='specific-profile'),
]
