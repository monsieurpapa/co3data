from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

class Region(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = _("Region")
        verbose_name_plural = _("Regions")

    def __str__(self):
        return self.name

class User(AbstractUser):
    # Custom user model extending Django's AbstractUser
    USER_ROLES = (
        ('member', _('Cooperative Member')),
        ('manager', _('Cooperative Manager')),
        ('regional_officer', _('Regional Officer')),
        ('apex_body', _('Apex Body Representative')),
        ('government', _('Government Official')),
        ('admin', _('System Administrator')),
    )
    role = models.CharField(max_length=20, choices=USER_ROLES, default='member')
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    region = models.ForeignKey(Region, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")

    def __str__(self):
        return self.username
