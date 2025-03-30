from django.db.models.signals import post_save
from django.dispatch import receiver
from accounts.models import User
from .models import ProviderProfile

@receiver(post_save, sender=User)
def create_provider_profile(sender, instance, created, **kwargs):
    if created and instance.role == User.Role.SERVICE_PROVIDER:
        ProviderProfile.objects.create(user=instance)
