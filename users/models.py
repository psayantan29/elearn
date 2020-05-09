from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import AbstractUser
# from django_mysql.models import ListCharField


class UserProfile(AbstractUser):
    is_professor = models.BooleanField(default=False)
    is_site_admin = models.BooleanField(default=False)
    # List_courses = models.ListCharField(
    #     base_field=models.Charfield(maxlength=30),
    #     size=20,
    #     max_length=20*30)
    # is_affiliate = models.BooleanField(default=False)
    # parent=models.CharField(max_length=20)
