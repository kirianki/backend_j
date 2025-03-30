from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action  # Add this import
from .models import Booking, Report, Favorite
from .serializers import BookingSerializer, ReportSerializer, FavoriteSerializer
from accounts.models import User  # Added import

class BookingViewSet(viewsets.ModelViewSet):
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        provider_id = self.request.query_params.get('provider')  # New: Get provider filter
        
        if user.role == User.Role.CLIENT:
            queryset = Booking.objects.filter(client=user)
            if provider_id:  # New: Client filtering by provider
                queryset = queryset.filter(provider__id=provider_id)
        elif user.role == User.Role.SERVICE_PROVIDER and hasattr(user, 'providerprofile'):
            queryset = Booking.objects.filter(provider=user.providerprofile)  # Providers always see their own
        elif user.is_staff:
            queryset = Booking.objects.all()
            if provider_id:  # New: Staff filtering by provider
                queryset = queryset.filter(provider__id=provider_id)
        else:
            queryset = Booking.objects.none()
        
        return queryset.order_by('-created_at')

    # New actions for confirm/cancel
    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        if request.user.role != User.Role.SERVICE_PROVIDER or not hasattr(request.user, 'providerprofile'):
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        booking = self.get_object()
        if booking.status != 'pending':
            return Response({'error': 'Booking can only be confirmed if pending'}, status=status.HTTP_400_BAD_REQUEST)
        booking.status = 'confirmed'
        booking.save()
        return Response(self.get_serializer(booking).data)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        booking = self.get_object()
        
        # Check if the user is a service provider or the client who owns the booking
        if request.user.role == User.Role.SERVICE_PROVIDER and hasattr(request.user, 'providerprofile'):
            if booking.provider != request.user.providerprofile:
                return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        elif request.user.role == User.Role.CLIENT:
            if booking.client != request.user:
                return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        else:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        # Ensure the booking is in a pending state
        if booking.status != 'pending':
            return Response({'error': 'Booking can only be cancelled if pending'}, status=status.HTTP_400_BAD_REQUEST)
        
        booking.status = 'cancelled'
        booking.save()
        return Response(self.get_serializer(booking).data)

class ReportViewSet(viewsets.ModelViewSet):
    serializer_class = ReportSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff:
            return Report.objects.all().order_by('-created_at')
        return Report.objects.filter(reporter=self.request.user).order_by('-created_at')

class FavoriteViewSet(viewsets.ModelViewSet):
    serializer_class = FavoriteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Favorite.objects.filter(user=self.request.user).order_by('-added_at')
