from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProviderProfileViewSet, SectorViewSet, SubcategoryViewSet, ReviewViewSet

router = DefaultRouter()
router.register(r'providers', ProviderProfileViewSet, basename='provider')
router.register(r'sectors', SectorViewSet, basename='sector')
router.register(r'subcategories', SubcategoryViewSet, basename='subcategory')
router.register(r'reviews', ReviewViewSet, basename='review')

urlpatterns = [
    path('', include(router.urls)),
]
