from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom user for the dashboard. Analysts review alerts; admins can also
    manage other users. Kept minimal — auth is handled by Django + SimpleJWT.
    """

    class Role(models.TextChoices):
        ANALYST = "analyst", "Analyst"
        ADMIN = "admin", "Admin"

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.ANALYST,
    )

    def __str__(self) -> str:
        return f"{self.username} ({self.role})"
