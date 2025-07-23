from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    # 可扩展字段，如手机号等
    phone = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return self.username