from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models

class UserManager(BaseUserManager):
    def create_user(self, username, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set.")
        email = self.normalize_email(email)
        extra_fields.setdefault('role', User.Role.CLIENT)
        user = self.model(username=username, email=email, **extra_fields)
        if not password:
            raise ValueError("Password must be provided.")
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Superuser must have an email.")
        extra_fields.setdefault('role', User.Role.OVERALL_ADMIN)
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(username, email, password, **extra_fields)

class User(AbstractUser):
    class Role(models.TextChoices):
        OVERALL_ADMIN = 'overall_admin', 'Overall Admin'
        SECTOR_ADMIN = 'sector_admin', 'Sector Admin'
        SERVICE_PROVIDER = 'service_provider', 'Service Provider'
        CLIENT = 'client', 'Client'

    email = models.EmailField(unique=True)
    username = models.CharField(max_length=150, unique=True)
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        db_index=True,
        default=Role.CLIENT
    )
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)

    objects = UserManager()

    def __str__(self):
        return f"{self.username} ({self.get_role_display() if self.role else 'Unknown Role'}) - {self.email}"

class ActivityLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="activity_logs")
    action = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.action} at {self.timestamp}"