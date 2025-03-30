from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from .models import Message, Notification, Conversation
from .serializers import MessageSerializer, NotificationSerializer, ConversationSerializer
from rest_framework.pagination import PageNumberPagination

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 10000

class MessageViewSet(viewsets.ModelViewSet):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_fields = ['is_read', 'created_at']
    ordering_fields = ['created_at']
    search_fields = ['content']

    def get_queryset(self):
        user = self.request.user
        return Message.objects.filter(Q(sender=user) | Q(receiver=user))

    def perform_create(self, serializer):
        sender = self.request.user
        receiver = serializer.validated_data.get("receiver")
        participant_one, participant_two = sorted([sender, receiver], key=lambda u: u.id)
        conversation, created = Conversation.objects.get_or_create(
            participant_one=participant_one, participant_two=participant_two
        )
        serializer.save(sender=sender, conversation=conversation)

    @action(detail=False, methods=['get'], url_path='received')
    def received_messages(self, request):
        """
        Get messages where the authenticated user is the receiver.
        Optionally mark them as read by passing ?mark_read=true in the request.
        """
        messages = Message.objects.filter(receiver=request.user)
        if request.query_params.get("mark_read", "").lower() == "true":
            messages.update(is_read=True)
        page = self.paginate_queryset(messages)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(messages, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'], url_path='mark-read/(?P<user_id>\d+)')
    def mark_read(self, request, user_id=None):
        """
        Mark all messages for the specified user as read.
        URL format: /communications/messages/mark-read/<user_id>/
        """
        # Verify the requesting user is the same as the user_id or add permission checks if needed
        if request.user.id != int(user_id):
            return Response({"error": "You can only mark your own messages as read."}, 
                          status=status.HTTP_403_FORBIDDEN)
        
        updated_count = Message.objects.filter(receiver=request.user, is_read=False).update(is_read=True)
        return Response({
            "message": f"Successfully marked {updated_count} messages as read.",
            "marked_count": updated_count
        }, status=status.HTTP_200_OK)

class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)

    @action(detail=False, methods=['post'], url_path='mark-read')
    def mark_read(self, request):
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return Response({"message": "Notifications marked as read."}, status=status.HTTP_200_OK)

class ConversationViewSet(viewsets.ModelViewSet):
    serializer_class = ConversationSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        user = self.request.user
        return Conversation.objects.filter(Q(participant_one=user) | Q(participant_two=user))

    @action(detail=True, methods=['get'], url_path='messages')
    def conversation_messages(self, request, pk=None):
        conversation = self.get_object()
        messages = Message.objects.filter(conversation=conversation).order_by("created_at")
        page = self.paginate_queryset(messages)
        if page is not None:
            serializer = MessageSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data)
