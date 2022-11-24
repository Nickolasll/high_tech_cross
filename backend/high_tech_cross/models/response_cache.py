from django.db import models


class ResponseCache(models.Model):
    """
    Запись успешной обработки запроса с попыткой решения задания.
    Необходима для надежности в случаях обрыва интернет соединения.
    """
    request_id = models.UUIDField(primary_key=True, editable=False)
    success = models.BooleanField()
