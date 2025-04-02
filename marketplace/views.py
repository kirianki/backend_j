from django.contrib.gis.geos import Point
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.measure import Distance as D
from django_filters.rest_framework import DjangoFilterBackend, FilterSet, NumberFilter
from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import ProviderProfile, Sector, Subcategory, Review, PortfolioMedia
from .serializers import (
    ProviderProfileSerializer, 
    SectorSerializer, 
    SubcategorySerializer, 
    ReviewSerializer,
    PortfolioMediaSerializer
)
from accounts.permissions import IsOwner, IsServiceProvider
from accounts.models import User
import logging
from rest_framework.pagination import PageNumberPagination
from django.db import transaction, models
from django.db.models import Avg, Q

class ProviderPagination(PageNumberPagination):
    page_size = 30
    page_size_query_param = 'page_size'
    max_page_size = 20000

logger = logging.getLogger(__name__)

class ReviewFilter(FilterSet):
    min_rating = NumberFilter(field_name='rating', lookup_expr='gte')
    max_rating = NumberFilter(field_name='rating', lookup_expr='lte')
    
    class Meta:
        model = Review
        fields = {
            'rating': ['exact'],
            'is_approved': ['exact'],
            'provider': ['exact'],
        }

class ProviderProfileFilter(FilterSet):
    min_avg_rating = NumberFilter(method='filter_min_avg_rating')
    max_avg_rating = NumberFilter(method='filter_max_avg_rating')
    min_reviews_count = NumberFilter(method='filter_min_reviews_count')
    
    class Meta:
        model = ProviderProfile
        fields = {
            'is_verified': ['exact'],
            'county': ['exact'],
            'subcounty': ['exact'],
            'town': ['exact'],
            'sector': ['exact'],
            'subcategory': ['exact'],
            'membership_tier': ['exact'],
            'is_featured': ['exact'],
        }
    
    def filter_min_avg_rating(self, queryset, name, value):
        try:
            value = float(value)
            return queryset.annotate(
                avg_rating=Avg('reviews__rating')
            ).filter(avg_rating__gte=value)
        except (ValueError, TypeError):
            return queryset
    
    def filter_max_avg_rating(self, queryset, name, value):
        try:
            value = float(value)
            return queryset.annotate(
                avg_rating=Avg('reviews__rating')
            ).filter(avg_rating__lte=value)
        except (ValueError, TypeError):
            return queryset
    
    def filter_min_reviews_count(self, queryset, name, value):
        try:
            value = int(value)
            return queryset.annotate(
                reviews_count=models.Count('reviews')
            ).filter(reviews_count__gte=value)
        except (ValueError, TypeError):
            return queryset

class ProviderProfileViewSet(viewsets.ModelViewSet):
    serializer_class = ProviderProfileSerializer
    pagination_class = ProviderPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ProviderProfileFilter
    search_fields = ['business_name', 'description', 'tags']
    ordering_fields = ['updated_at', 'is_verified', 'business_name', 'avg_rating', 'reviews_count']

    def get_queryset(self):
        queryset = ProviderProfile.objects.select_related('user', 'sector', 'subcategory') \
            .prefetch_related('portfolio_media') \
            .annotate(
                avg_rating=Avg('reviews__rating'),
                reviews_count=models.Count('reviews')
            )
        
        if 'min_avg_rating' in self.request.query_params:
            queryset = queryset.filter(reviews__isnull=False).distinct()
            
        return queryset

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated(), IsServiceProvider(), IsOwner()]
        return [permissions.AllowAny()]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'], url_path='by-user/(?P<user_id>[^/.]+)')
    def get_by_user(self, request, user_id=None):
        try:
            provider_profile = ProviderProfile.objects.get(user__id=user_id)
            serializer = self.get_serializer(provider_profile)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except ProviderProfile.DoesNotExist:
            return Response({"error": "Provider profile not found."}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['get'], url_path='featured')
    def featured_providers(self, request):
        lat = request.query_params.get('lat')
        lng = request.query_params.get('lng')
        radius = request.query_params.get('radius')
        min_avg_rating = request.query_params.get('min_avg_rating')
        
        if not all([lat, lng, radius]):
            return Response({"error": "lat, lng and radius parameters are required."},
                            status=status.HTTP_400_BAD_REQUEST)
        try:
            lat, lng, radius = float(lat), float(lng), float(radius)
            if min_avg_rating:
                min_avg_rating = float(min_avg_rating)
        except ValueError:
            return Response({"error": "Invalid parameter value."},
                            status=status.HTTP_400_BAD_REQUEST)
        
        point = Point(lng, lat, srid=4326)
        providers = self.get_queryset().filter(
            is_featured=True,
            location__distance_lte=(point, D(km=radius))
        )
        
        if min_avg_rating:
            providers = providers.filter(avg_rating__gte=min_avg_rating)
            
        providers = providers.annotate(distance=Distance('location', point)).order_by('distance')
        serializer = self.get_serializer(providers, many=True)
        return Response(serializer.data)

    # Portfolio Media Endpoints
    @action(detail=True, methods=['get', 'post'], url_path='portfolio-media')
    def portfolio_media(self, request, pk=None):
        provider = self.get_object()
        
        if request.method == 'GET':
            media = provider.portfolio_media.all()
            serializer = PortfolioMediaSerializer(media, many=True)
            return Response(serializer.data)
            
        elif request.method == 'POST':
            if not request.user == provider.user:
                return Response(
                    {"error": "You can only add media to your own profile"},
                    status=status.HTTP_403_FORBIDDEN
                )
            serializer = PortfolioMediaSerializer(data=request.data, context={'request': request})
            if serializer.is_valid():
                serializer.save(provider=provider)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get', 'patch', 'delete'], url_path='portfolio-media/(?P<media_id>[^/.]+)')
    def single_portfolio_media(self, request, pk=None, media_id=None):
        provider = self.get_object()
        
        try:
            media = provider.portfolio_media.get(id=media_id)
        except PortfolioMedia.DoesNotExist:
            return Response({"error": "Media not found"}, status=status.HTTP_404_NOT_FOUND)
            
        if request.method == 'GET':
            serializer = PortfolioMediaSerializer(media)
            return Response(serializer.data)
            
        elif request.method == 'PATCH':
            if not request.user == provider.user:
                return Response(
                    {"error": "You can only edit media in your own profile"},
                    status=status.HTTP_403_FORBIDDEN
                )
            serializer = PortfolioMediaSerializer(media, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        elif request.method == 'DELETE':
            if not request.user == provider.user:
                return Response(
                    {"error": "You can only delete media from your own profile"},
                    status=status.HTTP_403_FORBIDDEN
                )
            media.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

class SectorViewSet(viewsets.ModelViewSet):
    serializer_class = SectorSerializer
    queryset = Sector.objects.all()
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'bulk_create_with_categories']:
            return [permissions.IsAuthenticated(), permissions.IsAdminUser()]
        return [permissions.AllowAny()]

    @action(detail=False, methods=['post'], url_path='bulk-create-with-categories')
    def bulk_create_with_categories(self, request):
        sectors_data = request.data
        if not isinstance(sectors_data, list):
            return Response({"error": "Expected a list of sectors."}, status=status.HTTP_400_BAD_REQUEST)
        
        sector_names = [sector.get('name') for sector in sectors_data]
        
        with transaction.atomic():
            new_sector_objs = []
            for sector in sectors_data:
                new_sector_objs.append(Sector(
                    name=sector.get('name'),
                    description=sector.get('description')
                ))
            Sector.objects.bulk_create(new_sector_objs)
            
            sectors_mapping = {s.name: s for s in Sector.objects.filter(name__in=sector_names)}
            
            subcategory_objs = []
            for sector in sectors_data:
                sector_name = sector.get('name')
                sector_instance = sectors_mapping.get(sector_name)
                if not sector_instance:
                    continue
                categories = sector.get('categories', [])
                for cat in categories:
                    subcategory_objs.append(Subcategory(
                        name=cat.get('name'),
                        description=cat.get('description'),
                        sector=sector_instance
                    ))
            Subcategory.objects.bulk_create(subcategory_objs)
        
        serializer = self.get_serializer(Sector.objects.filter(name__in=sector_names), many=True)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class SubcategoryViewSet(viewsets.ModelViewSet):
    serializer_class = SubcategorySerializer
    queryset = Subcategory.objects.all()
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated(), permissions.IsAdminUser()]
        return [permissions.AllowAny()]

class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer
    queryset = Review.objects.select_related('provider', 'client').all()
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_class = ReviewFilter
    search_fields = ['comment']
    ordering_fields = ['created_at', 'upvotes', 'rating']

    def get_permissions(self):
        if self.action == 'create':
            from accounts.permissions import IsClient
            return [permissions.IsAuthenticated(), IsClient()]
        elif self.action in ['update', 'partial_update', 'destroy', 'respond']:
            return [permissions.IsAuthenticated(), IsOwner()]
        return [permissions.AllowAny()]

    def perform_create(self, serializer):
        serializer.save(client=self.request.user)

    @action(detail=False, methods=['get'], url_path='provider/(?P<provider_id>[^/.]+)')
    def get_reviews_by_provider(self, request, provider_id=None):
        reviews = self.queryset.filter(provider_id=provider_id)
        serializer = self.get_serializer(reviews, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['patch'], url_path='respond')
    def respond(self, request, pk=None):
        review = self.get_object()
        if not hasattr(request.user, 'providerprofile') or review.provider.user != request.user:
            return Response(
                {"error": "Permission denied. You can only respond to your own reviews."},
                status=status.HTTP_403_FORBIDDEN
            )
        response_text = request.data.get('provider_response')
        if not response_text:
            return Response({"error": "No response provided."}, status=status.HTTP_400_BAD_REQUEST)
        review.provider_response = response_text
        review.save()
        serializer = self.get_serializer(review)
        return Response(serializer.data, status=status.HTTP_200_OK)