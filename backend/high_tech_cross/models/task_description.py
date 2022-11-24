import uuid

from django.db import models
from django_better_admin_arrayfield.models.fields import ArrayField


class TaskDescription(models.Model):
    """
    Модель описания задания.
    Здесь задается описательная часть задачи, координаты, подсказки и ответ.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=300)
    coordinates = ArrayField(base_field=models.CharField(max_length=10), size=2)
    description = models.CharField(max_length=300)
    answer = models.CharField(max_length=30)
    hints = ArrayField(base_field=models.CharField(max_length=300), size=3)

    def __str__(self):
        return f"{self.name} - {self.description}" if self.name or self.description else str(self.id)

    @property
    def max_hints(self) -> int:
        return len(self.hints)
