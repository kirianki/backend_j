import logging
from django.contrib.auth import get_user_model
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import RegisterSerializer, UserSerializer, ProfileUpdateSerializer
from .models import ActivityLog
from rest_framework.exceptions import NotFound
from django.core.exceptions import ObjectDoesNotExist
import logging


class SpecificUserProfileView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]  # Or AllowAny if public access is needed
    serializer_class = UserSerializer

    def get_object(self):
        user_id = self.kwargs.get('user_id')
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise NotFound("User not found")

User = get_user_model()
logger = logging.getLogger(__name__)

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        # Embed extra metadata for role and onboarding checks
        data.update({
            "user_id": self.user.id,
            "username": self.user.username,
            "email": self.user.email,
            "role": self.user.role,
            "role_display": self.user.get_role_display(),
            # Additional metadata can be added if needed.
        })
        return data

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        return Response({
            "message": "User registered successfully!",
            "user": response.data
        }, status=response.status_code)

class UserProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            # Pass request context to serializer for absolute URLs
            serializer = UserSerializer(request.user, context={'request': request})
            return Response(serializer.data)
        except Exception as e:
            logger.error("Error fetching user profile: %s", str(e))
            return Response(
                {"error": "Failed to fetch profile data"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def put(self, request):
        try:
            data = request.data.copy()
            profile_picture = request.FILES.get('profile_picture')
            
            # Handle file upload
            if profile_picture:
                # Validate file size (e.g., 5MB max)
                if profile_picture.size > 5 * 1024 * 1024:
                    return Response(
                        {"profile_picture": "File size too large. Max 5MB allowed."},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                data['profile_picture'] = profile_picture
            elif 'profile_picture' in data and data['profile_picture'] == 'null':
                # Handle profile picture removal
                data['profile_picture'] = None

            # Pass request context to serializer
            serializer = ProfileUpdateSerializer(
                request.user,
                data=data,
                partial=True,
                context={'request': request}
            )

            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            serializer.save()

            # Create audit log
            ActivityLog.objects.create(
                user=request.user,
                action="Updated profile",
                metadata={
                    'updated_fields': list(data.keys()),
                    'ip_address': request.META.get('REMOTE_ADDR')
                }
            )

            logger.info(
                "User %s updated their profile. Updated fields: %s",
                request.user.username,
                list(data.keys())
            )

            return Response({
                "message": "Profile updated successfully",
                "user": UserSerializer(request.user, context={'request': request}).data
            })

        except ObjectDoesNotExist:
            logger.error("User not found during profile update")
            return Response(
                {"error": "User not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error("Error updating profile: %s", str(e))
            return Response(
                {"error": "An error occurred while updating profile"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response({"error": "Refresh token is required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"message": "Logout successful."}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.exception("Error blacklisting token: %s", e)
            return Response({"error": "Invalid or expired token."}, status=status.HTTP_400_BAD_REQUEST)
