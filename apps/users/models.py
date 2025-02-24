from django.db import models
from django.contrib.auth.models import AbstractUser
from ..restaurants.models import Restaurant


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'ADMIN', 'Admin'
        WAITRESS = 'WAITRESS', 'Waitress'
        OWNER = 'OWNER', 'Owner'

    groups = models.ManyToManyField(
        'auth.Group',
        related_name='custom_user_set',
        blank=True,
        help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.',
        verbose_name='groups',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='custom_user_set',
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )

    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.ADMIN
    )
    restaurant = models.ForeignKey(Restaurant,
                                    on_delete=models.SET_NULL,
                                    null=True,
                                    blank=True,
                                    related_name='employees')
    status = models.BooleanField(default=True)

    class Meta:
        ordering = ['username']


class Client(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    status = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name