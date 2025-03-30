from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from accounts.models import User
from django.utils.timezone import now
from django.contrib.auth import get_user_model

User = get_user_model()

class Conversation(models.Model):
    # Temporarily providing a default value of 1 to avoid migration errors.
    # Ensure a user with id=1 exists or update this default accordingly.
    participant_one = models.ForeignKey(
        User,
        related_name="conversations_as_participant_one",
        on_delete=models.CASCADE,
        default=1,
    )
    participant_two = models.ForeignKey(
        User,
        related_name="conversations_as_participant_two",
        on_delete=models.CASCADE,
        default=1,
    )
    created_at = models.DateTimeField(default=now)

    def __str__(self):
        return f"Conversation between {self.participant_one} and {self.participant_two}"

class Message(models.Model):
    conversation = models.ForeignKey(
        Conversation,
        related_name="messages",
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    sender = models.ForeignKey(
        User,
        related_name="sent_messages",
        on_delete=models.CASCADE
    )
    receiver = models.ForeignKey(
        User,
        related_name="received_messages",
        on_delete=models.CASCADE
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        """Automatically associate the message with a conversation if not provided."""
        if not self.conversation:
            participant_one, participant_two = sorted([self.sender, self.receiver], key=lambda u: u.id)
            conversation, created = Conversation.objects.get_or_create(
                participant_one=participant_one, participant_two=participant_two
            )
            self.conversation = conversation
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Message from {self.sender.username} to {self.receiver.username}"

class Notification(models.Model):
    user = models.ForeignKey(
        User,
        related_name="notifications",
        on_delete=models.CASCADE
    )
    message = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification for {self.user.username}"

@receiver(post_save, sender=Message)
def create_notification_on_message(sender, instance, created, **kwargs):
    if created:
        snippet = instance.content[:50] + ("..." if len(instance.content) > 50 else "")
        Notification.objects.create(
            user=instance.receiver,
            message=f"New message from {instance.sender.username}: {snippet}"
        )
