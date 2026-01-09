from django.db import models

# Create your models here.
class User(models.Model):
    ROLE_CHOICES = (
        ('citizen', 'Citizen'),
        ('admin', 'Admin'),
    )
    username = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)

    is_super_admin = models.BooleanField(default=False)  # ⭐

    created_at = models.DateTimeField(auto_now_add=True)
