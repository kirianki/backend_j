import json
import logging
from urllib.parse import parse_qs
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from rest_framework_simplejwt.tokens import AccessToken
from accounts.models import User
from .models import Message, Conversation

logger = logging.getLogger(__name__)

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        """Authenticate user and extract receiver_id."""
        query_string = parse_qs(self.scope["query_string"].decode())
        token = query_string.get("token", [None])[0]
        if not token:
            logger.warning("WebSocket connection attempt without token.")
            await self.close()
            return

        self.user = await self.get_user_from_token(token)
        if not self.user:
            logger.warning("Invalid or expired token.")
            await self.close()
            return

        try:
            self.receiver_id = int(self.scope["url_route"]["kwargs"]["receiver_id"])
        except (KeyError, ValueError, TypeError):
            logger.error("Invalid or missing receiver_id in WebSocket URL.")
            await self.close()
            return

        receiver_exists = await self.user_exists(self.receiver_id)
        if not receiver_exists:
            logger.error("Receiver does not exist.")
            await self.close()
            return

        # Retrieve or create a conversation between the two users.
        self.conversation = await self.get_or_create_conversation(self.user.id, self.receiver_id)
        self.room_group_name = f"chat_{self.conversation.id}"

        # Join the chat group.
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        """Leave the chat group on disconnect."""
        if hasattr(self, "room_group_name"):
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        """Receive a message, save it, and broadcast it to the group."""
        data = json.loads(text_data)
        message = data.get("message")
        if not message:
            return  # Ignore empty messages

        # Save message to DB.
        await self.save_message(self.user.id, self.receiver_id, message, self.conversation.id)

        # Send the message to the group.
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "message": message,
                "sender_id": self.user.id
            }
        )

    async def chat_message(self, event):
        """Send the received message to WebSocket clients."""
        await self.send(text_data=json.dumps({
            "sender_id": event["sender_id"],
            "message": event["message"]
        }))

    @database_sync_to_async
    def get_user_from_token(self, token):
        """Validate and extract user from JWT token."""
        try:
            access_token = AccessToken(token)
            return User.objects.get(id=access_token["user_id"])
        except Exception as e:
            logger.error("Token validation failed: %s", e)
            return None

    @database_sync_to_async
    def user_exists(self, user_id):
        """Check if a user exists."""
        return User.objects.filter(id=user_id).exists()

    @database_sync_to_async
    def get_or_create_conversation(self, sender_id, receiver_id):
        """Retrieve an existing conversation or create a new one based on sorted user IDs."""
        sender = User.objects.get(id=sender_id)
        receiver = User.objects.get(id=receiver_id)
        participant_one, participant_two = sorted([sender, receiver], key=lambda u: u.id)
        conversation, created = Conversation.objects.get_or_create(
            participant_one=participant_one, participant_two=participant_two
        )
        return conversation

    @database_sync_to_async
    def save_message(self, sender_id, receiver_id, message, conversation_id):
        """Save a new message to the database."""
        sender = User.objects.get(id=sender_id)
        receiver = User.objects.get(id=receiver_id)
        conversation = Conversation.objects.get(id=conversation_id)
        Message.objects.create(sender=sender, receiver=receiver, content=message, conversation=conversation)
