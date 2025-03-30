from rest_framework import serializers
from .models import Message, Notification, Conversation

class MessageSerializer(serializers.ModelSerializer):
    sender = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = ['id', 'sender', 'receiver', 'conversation', 'content', 'created_at', 'is_read']

    def get_sender(self, obj):
        return {
            "id": obj.sender.id,
            "username": obj.sender.username,
        }

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'user', 'message', 'is_read', 'created_at']

class ConversationSerializer(serializers.ModelSerializer):
    participant_one = serializers.PrimaryKeyRelatedField(read_only=True)
    participant_two = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Conversation
        fields = ['id', 'participant_one', 'participant_two', 'created_at']
