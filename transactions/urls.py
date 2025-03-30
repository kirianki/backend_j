from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BookingViewSet, ReportViewSet, FavoriteViewSet

router = DefaultRouter()
router.register(r'bookings', BookingViewSet, basename='booking')
router.register(r'reports', ReportViewSet, basename='report')
router.register(r'favorites', FavoriteViewSet, basename='favorite')

urlpatterns = [
    path('', include(router.urls)),
]
