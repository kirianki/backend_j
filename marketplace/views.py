from django.contrib.gis.geos import Point
from django.contrib.gis.db.models.functions import Distance  # for annotations
from django.contrib.gis.measure import Distance as D        # for filtering
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import ProviderProfile, Sector, Subcategory, Review
from .serializers import ProviderProfileSerializer, SectorSerializer, SubcategorySerializer, ReviewSerializer
from accounts.permissions import IsOwner, IsServiceProvider
from accounts.models import User
import logging
from rest_framework.pagination import PageNumberPagination
from django.db import transaction

class ProviderPagination(PageNumberPagination):
    page_size = 30  # Customize the number of results per page
    page_size_query_param = 'page_size'
    max_page_size = 20000

logger = logging.getLogger(__name__)

class ProviderProfileViewSet(viewsets.ModelViewSet):
    serializer_class = ProviderProfileSerializer
    pagination_class = ProviderPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_verified', 'county', 'subcounty', 'town', 'sector', 'subcategory', 'membership_tier']
    search_fields = ['business_name', 'description', 'tags']
    ordering_fields = ['updated_at', 'is_verified', 'business_name']

    def get_queryset(self):
        # Use select_related for related single-valued fields and prefetch_related for portfolio_media.
        return ProviderProfile.objects.select_related('user', 'sector', 'subcategory').prefetch_related('portfolio_media').all()

    def get_permissions(self):
        # Only service providers who are the owner can create/update their provider profiles.
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
        if not all([lat, lng, radius]):
            return Response({"error": "lat, lng and radius parameters are required."},
                            status=status.HTTP_400_BAD_REQUEST)
        try:
            lat, lng, radius = float(lat), float(lng), float(radius)
        except ValueError:
            return Response({"error": "Invalid lat, lng or radius value."},
                            status=status.HTTP_400_BAD_REQUEST)
        point = Point(lng, lat, srid=4326)
        providers = self.get_queryset().filter(
            is_featured=True,
            location__distance_lte=(point, D(km=radius))
        ).annotate(distance=Distance('location', point)).order_by('distance')
        serializer = self.get_serializer(providers, many=True)
        return Response(serializer.data)

class SectorViewSet(viewsets.ModelViewSet):
    serializer_class = SectorSerializer
    queryset = Sector.objects.all()
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'bulk_create_with_categories']:
            return [permissions.IsAuthenticated(), permissions.IsAdminUser()]
        return [permissions.AllowAny()]  # Anyone can view sectors

    @action(detail=False, methods=['post'], url_path='bulk-create-with-categories')
    def bulk_create_with_categories(self, request):
        """
        Expects a JSON array of sectors, each with a nested "categories" list.
        Example payload:
        [
            {
                "name": "IT Sector",
                "description": "Technology and software services.",
                "categories": [
                    {"name": "Software Development", "description": "Custom software solutions."},
                    {"name": "Cybersecurity", "description": "Protecting networks and data."},
                    {"name": "Cloud Computing", "description": "Cloud-based services."}
                ]
            },
            {
                "name": "Healthcare Sector",
                "description": "Medical services and products.",
                "categories": [
                    {"name": "Hospitals", "description": "General and specialized hospitals."},
                    {"name": "Clinics", "description": "Outpatient care centers."},
                    {"name": "Pharmaceuticals", "description": "Medicine manufacturing and distribution."}
                ]
            }
            // ... at least 10 sectors total with 3 categories each
        ]
        """
        sectors_data = request.data
        if not isinstance(sectors_data, list):
            return Response({"error": "Expected a list of sectors."}, status=status.HTTP_400_BAD_REQUEST)
        
        sector_names = [sector.get('name') for sector in sectors_data]
        
        with transaction.atomic():
            # Create new sectors in bulk. Note: This assumes sector names are unique.
            new_sector_objs = []
            for sector in sectors_data:
                new_sector_objs.append(Sector(
                    name=sector.get('name'),
                    description=sector.get('description')
                ))
            # Use bulk_create to insert new sectors.
            Sector.objects.bulk_create(new_sector_objs)
            
            # Retrieve all sectors (newly created or pre-existing) that match the provided names.
            sectors_mapping = {s.name: s for s in Sector.objects.filter(name__in=sector_names)}
            
            # Prepare subcategory objects for bulk creation.
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
        
        # Return the sectors created/updated.
        serializer = self.get_serializer(Sector.objects.filter(name__in=sector_names), many=True)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class SubcategoryViewSet(viewsets.ModelViewSet):
    serializer_class = SubcategorySerializer
    queryset = Subcategory.objects.all()
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated(), permissions.IsAdminUser()]
        return [permissions.AllowAny()]  # Anyone can view subcategories

class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer
    queryset = Review.objects.select_related('provider', 'client').all()
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_fields = ['rating', 'is_approved', 'provider']
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
        # Automatically set the client field from the authenticated user.
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
