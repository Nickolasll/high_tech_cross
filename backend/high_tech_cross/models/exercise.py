import uuid

from datetime import timedelta

from django.db import models
from django_better_admin_arrayfield.models.fields import ArrayField
from django.utils import timezone

from . import Team, Competition, TaskDescription, Rule

from .competition import CompetitionStatus
from ..application_context import ApplicationContext


class ExerciseStatus:
    DONE = 'Сдано'
    WRONG_ATTEMPTED = 'Попытка сдачи'
    NOT_STARTED = 'Не начато'
    HINT_USED = 'Начато'


class ExerciseManager(models.Manager):

    def all_team_exercises(self, team_id):
        competition_id = ApplicationContext().competition_id.get()
        return self.filter(team=team_id, competition=competition_id)


class Exercise(models.Model):
    """
    Модель процесса исполнения командой задания в рамках соревнования.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    used_hints = ArrayField(base_field=models.IntegerField(), size=3, null=True, default=list)
    wrong_attempts = models.IntegerField(default=0)
    completed_at = models.DateTimeField(default=None, null=True)

    # Связи исполнения задания с командой, соревнованием и самим описанием задания
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    competition = models.ForeignKey(Competition, on_delete=models.CASCADE)
    task_description = models.ForeignKey(TaskDescription, on_delete=models.CASCADE)

    objects = ExerciseManager()

    class Meta:
        index_together = ['team', 'competition']

    def check_answer(self, answer: str) -> bool:
        return self.task_description.answer == answer

    def _get_hint(self, hint_number: int) -> str:
        if hint_number not in self.used_hints:
            self.used_hints.append(hint_number)
        return self.task_description.hints[hint_number]

    def pick_hint(self, hint_number: int):
        if hint_number in self.used_hints:
            return self._get_hint(hint_number=hint_number)

        return self._get_hint(hint_number=hint_number)

    def is_hint_number_valid(self, hint_number: int) -> bool:
        """
        Проверяем доступность получения подсказки
        :param hint_number: номер подсказки
        :return:
        """
        return hint_number < len(self.task_description.hints)

    def attempt(self, answer: str) -> bool:
        success = self.check_answer(answer)
        if success:
            self.completed_at = timezone.now()
        else:
            self.wrong_attempts += 1
        return success

    @property
    def status(self) -> str:
        if self.completed_at:
            return ExerciseStatus.DONE
        elif self.wrong_attempts:
            return ExerciseStatus.WRONG_ATTEMPTED
        elif self.used_hints:
            return ExerciseStatus.HINT_USED
        else:
            return ExerciseStatus.NOT_STARTED

    @property
    def used_hints_count(self) -> int:
        return len(self.used_hints)

    @property
    def penalty_time(self) -> timedelta:
        return Rule.hint_penalty * self.used_hints_count + Rule.wrong_attempt_penalty * self.wrong_attempts

    @property
    def is_hint_available(self) -> bool:
        status = self.status
        if status == ExerciseStatus.DONE or self.competition.status != CompetitionStatus.IN_PROGRESS:
            is_hint_available = False
        else:
            is_hint_available = self.used_hints_count < self.task_description.max_hints
        return is_hint_available
