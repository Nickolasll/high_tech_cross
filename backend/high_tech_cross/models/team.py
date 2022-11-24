import uuid

from django.contrib.auth.hashers import make_password
from django.db import models


class TeamManager(models.Manager):
    def get_by_login(self, login: str):
        return self.filter(login=login).first()


class Team(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    login = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=30)
    password = models.CharField(max_length=100)

    objects = TeamManager()

    class Meta:
        indexes = [
            models.Index(fields=['login'], name='login_idx'),
        ]

    def __str__(self):
        return self.name if self.name else str(self.id)

    def save(self, *args, **kwargs):
        # сохраняем пароль в зашифрованном виде
        self.password = make_password(self.password)
        super().save(*args, **kwargs)
