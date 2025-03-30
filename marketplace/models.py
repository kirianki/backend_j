from django.db import models
from django.contrib.gis.db.models import PointField
from django.db.models import Avg
from accounts.models import User

class Sector(models.Model):
    name = models.CharField(max_length=100, unique=True, db_index=True)
    description = models.TextField(blank=True, null=True)
    thumbnail = models.ImageField(upload_to='sector_thumbnails/', blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Sector"
        verbose_name_plural = "Sectors"
        ordering = ['name']

    def __str__(self):
        return self.name

class Subcategory(models.Model):
    sector = models.ForeignKey(Sector, related_name='subcategories', on_delete=models.CASCADE)
    name = models.CharField(max_length=100, db_index=True)
    description = models.TextField(blank=True, null=True)
    thumbnail = models.ImageField(upload_to='subcategory_thumbnails/', blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('sector', 'name')
        ordering = ['name']
        verbose_name = "Subcategory"
        verbose_name_plural = "Subcategories"

    def __str__(self):
        return f"{self.name} ({self.sector.name})"

class ProviderProfile(models.Model):
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        limit_choices_to={'role': User.Role.SERVICE_PROVIDER}
    )
    location = PointField(geography=True, null=True, blank=True, srid=4326)
    address = models.CharField(max_length=255, blank=True, default='')
    business_name = models.CharField(max_length=255, blank=True, null=True)
    sector = models.ForeignKey(Sector, on_delete=models.PROTECT, db_index=True, null=True, blank=True)
    subcategory = models.ForeignKey(Subcategory, on_delete=models.PROTECT, db_index=True, null=True, blank=True)
    description = models.TextField(blank=True, default='')
    website = models.URLField(blank=True, null=True)
    county = models.CharField(max_length=100, blank=True, default='', db_index=True)
    subcounty = models.CharField(max_length=100, blank=True, default='', db_index=True)
    town = models.CharField(max_length=100, blank=True, default='', db_index=True)
    verification_document = models.FileField(upload_to='verification_docs/', blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    tags = models.CharField(max_length=255, blank=True, default='', help_text="Comma-separated keywords")
    is_featured = models.BooleanField(default=False, db_index=True)
    membership_tier = models.CharField(
        max_length=50, 
        choices=[('free', 'Free'), ('premium', 'Premium')],
        default='free'
    )
    recommended_providers = models.ManyToManyField(
        'self', 
        blank=True, 
        symmetrical=False,
        related_name='recommended_by'
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Service Provider"
        verbose_name_plural = "Service Providers"

    def __str__(self):
        return self.business_name or self.user.get_full_name() or self.user.username

    @property
    def average_rating(self):
        avg = self.reviews.aggregate(Avg('rating'))['rating__avg']
        return round(avg, 1) if avg else None

class PortfolioMedia(models.Model):
    MEDIA_CHOICES = (
        ('image', 'Image'),
        ('video', 'Video'),
    )
    provider = models.ForeignKey(ProviderProfile, related_name='portfolio_media', on_delete=models.CASCADE)
    media_type = models.CharField(max_length=10, choices=MEDIA_CHOICES)
    file = models.FileField(upload_to='portfolio_media/')
    caption = models.CharField(max_length=255, blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Portfolio Media"
        verbose_name_plural = "Portfolio Media"

    def __str__(self):
        return f"{self.get_media_type_display()} for {self.provider.business_name or self.provider.user.username}"

class Review(models.Model):
    provider = models.ForeignKey(ProviderProfile, related_name='reviews', on_delete=models.CASCADE)
    client = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': User.Role.CLIENT})
    rating = models.PositiveSmallIntegerField(db_index=True)
    comment = models.TextField(blank=True, default='')
    provider_response = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_approved = models.BooleanField(default=False)
    upvotes = models.PositiveIntegerField(default=0)
    downvotes = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Review"
        verbose_name_plural = "Reviews"

    def save(self, *args, **kwargs):
        if self.rating < 1 or self.rating > 5:
            raise ValueError("Rating must be between 1 and 5.")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Review ({self.rating}/5) by {self.client.username} on {self.provider}"
