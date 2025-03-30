from django.db import models
from accounts.models import User
from marketplace.models import ProviderProfile

class Booking(models.Model):
    client = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': User.Role.CLIENT})
    provider = models.ForeignKey(ProviderProfile, on_delete=models.CASCADE)
    service_date = models.DateTimeField()
    status = models.CharField(
        max_length=20,
        choices=[('pending', 'Pending'), ('confirmed', 'Confirmed'), ('cancelled', 'Cancelled')],
        default='pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Booking by {self.client.username} with {self.provider}"

class Report(models.Model):
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports')
    provider = models.ForeignKey(ProviderProfile, on_delete=models.CASCADE, related_name='reports')
    description = models.TextField()
    is_resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Report by {self.reporter.username} on {self.provider}"

class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites')
    provider = models.ForeignKey(ProviderProfile, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'provider')

    def __str__(self):
        return f"{self.user.username} favorited {self.provider}"
