import uuid

from datetime import timedelta, datetime

from django.utils import timezone
from django.db import models

from . import Team, TaskDescription
from .rule import Rule


class CompetitionStatus:
    NOT_STARTED = 'Не начато'
    IN_PROGRESS = 'В процессе'
    COMPLETED = 'Завершено'


class CompetitionManager(models.Manager):
    def get_nearest_competition_id(self, current_time: datetime, team_id: str) -> str:
        """
        Находим ближайшее к времени date соревнование.
        :param current_time:
        :param team_id:
        :return:
        """

        # Неприятная ситуация может произойти, если администратор наделает соревнований с промежутком менее времени
        # длительности соревнования, указанного в правиле Rule (То есть ситуация, в которой новое соревнование
        # начинается до того, как закончилось предыдущее, но эта команда участвует в обоих).

        # Это нужно ограничивать на этапе инициализации соревнования initialize_competition, но на данном
        # этапе реализации считаем, что администратор поступил нехорошо.

        competition = self.filter(teams=team_id, initialized=True, start_time__lte=current_time).order_by(
            '-start_time').first()
        # Если соревнование оказалось уже завершенным, ищем грядущее соревнование.
        if not competition or competition.status != CompetitionStatus.IN_PROGRESS:
            not_started = self.filter(teams=team_id, start_time__gt=current_time).order_by('-start_time').first()
            if not_started:
                competition = not_started
        return str(competition.id) if competition else None


class Competition(models.Model):
    """
    Модель описания соревнования
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=300)
    start_time = models.DateTimeField(default=timezone.now() + timedelta(hours=24))  # По умолчанию соревнование завтра

    # Храним связи соревнования с командой и соревнования с описанием задания в таком формате
    # Это сделано исключительно для удобства создания и инициализации соревнований в админке
    # Так и для агрегирования таблицы лидеров
    teams = models.ManyToManyField(Team)
    tasks = models.ManyToManyField(TaskDescription)

    # Только для чтения
    # Определяет - были ли инициализированы объекты прогресса исполнения заданий и таблица лидеров
    initialized = models.BooleanField(default=False)

    objects = CompetitionManager()

    class Meta:
        ordering = ['-start_time']
        indexes = [
            models.Index(fields=['initialized'], name='initialized_idx'),
        ]

    def __str__(self):
        return self.name if self.name else str(self.id)

    @property
    def status(self) -> str:
        """
        Вычисляем статус соревнования относительно времени time по обратному отсчету до начала и времени до конца.
        :return: Строка статуса соревнования
        """
        if not self.initialized:
            return CompetitionStatus.NOT_STARTED

        zero_delta = timedelta(0)

        if self.countdown != zero_delta:
            return CompetitionStatus.NOT_STARTED

        time_left = self.time_left
        if time_left != zero_delta:
            status = CompetitionStatus.IN_PROGRESS
        else:
            status = CompetitionStatus.COMPLETED

        return status

    @property
    def countdown(self) -> timedelta:
        """
        Вычисляем обратный отсчет до начала соревнования относительно времени time.
        :return: дельта до начала соревнования
        """
        zero_delta = timedelta(0)
        countdown = self.start_time - timezone.now()
        return zero_delta if countdown < zero_delta else countdown

    @property
    def end_time(self) -> datetime:
        return self.start_time + Rule.competition_duration

    @property
    def time_left(self) -> timedelta:
        """
        Вычисляем оставшееся время соревнования относительно времени time.
        :return: Дельта до завершения соревнования
        """
        zero_delta = timedelta(0)

        if self.countdown != zero_delta:
            time_left = Rule.competition_duration
        else:
            time_left = self.end_time - timezone.now()
            time_left = zero_delta if time_left < zero_delta else time_left

        return time_left
