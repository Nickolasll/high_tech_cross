from abc import ABCMeta

from django.db import transaction
from django.core.handlers.wsgi import WSGIRequest
from django.http.response import HttpResponse

from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.response import Response

from .abstract_api_view import AbstractAPIView

from ..models import Exercise, ResponseCache
from ..models.competition import CompetitionStatus
from ..models.exercise import ExerciseStatus
from ..serializers import ExerciseSerializer
from ..application_context import ApplicationContext
from ..models import Competition
from ..serializers.exercise_serializer import ExerciseHintValidation, ExerciseSolveValidation


class AbstractExerciseView(AbstractAPIView, metaclass=ABCMeta):
    serializer = ExerciseSerializer

    def validate_competition_state(self):
        """
        Проверяем состояние соревнования, чтобы определить, можем мы выполнять действие, или нет.
        :return: возвращаем competition, чтобы было проще делать дополнительные проверки в дочерних классах.
        """
        competition_id = ApplicationContext.competition_id.get()
        competition = self.get_object_or_404(
            Competition, not_found_message='Соревнование не найдено', pk=competition_id
        )
        if competition.status == CompetitionStatus.NOT_STARTED:
            message = 'Соревнование еще не начато, во избежание спойлеров вы не можете ни смотреть, ' \
                      'ни работать с заданиями'
            raise PermissionDenied(message)


class ExerciseView(AbstractExerciseView):
    http_method_names = ['get']
    serializer = ExerciseSerializer

    def get(self, request: WSGIRequest, exercise_id: str = None) -> HttpResponse:
        self.validate_competition_state()
        team_id = ApplicationContext.team_id.get()
        competition_id = ApplicationContext.competition_id.get()
        if exercise_id:
            exercise = self.get_object_or_404(
                Exercise,
                not_found_message=f'Задание {exercise_id} не найдено',
                competition=competition_id,
                team=team_id,
                id=exercise_id
            )
            return Response(data=self.serializer(exercise).data)
        exercises = self.get_list_or_404(
            Exercise,
            not_found_message='Заданий не найдено',
            competition=competition_id,
            team=team_id
        )
        return Response(data=self.serializer(exercises, many=True).data)


class AbstractExercisePostView(AbstractExerciseView, metaclass=ABCMeta):
    http_method_names = ['post']

    def validate_competition_state(self):
        """
        Переопределение поведения проверки состояния соревнования.
        В данном случае необходимо дополнительно проверять, не закончилось ли соревнование.
        :return:
        """
        competition_id = ApplicationContext.competition_id.get()
        competition = self.get_object_or_404(
            Competition, not_found_message='Соревнование не найдено', pk=competition_id
        )
        status = competition.status
        if status == CompetitionStatus.NOT_STARTED:
            message = 'Соревнование еще не начато, во избежание спойлеров вы не можете ни смотреть, ' \
                      'ни работать с заданиями'
            raise PermissionDenied(message)
        elif status != CompetitionStatus.IN_PROGRESS:
            raise PermissionDenied('Соревнование уже закончилось')


class ExerciseHintView(AbstractExercisePostView):
    validator = ExerciseHintValidation

    def _post(self, exercise_id: str, number: int) -> HttpResponse:
        self.validate_competition_state()
        team_id = ApplicationContext.team_id.get()
        competition_id = ApplicationContext.competition_id.get()
        exercise = self.get_object_or_404(
            Exercise,
            not_found_message=f'Задание {exercise_id} не найдено',
            competition=competition_id,
            team=team_id,
            id=exercise_id
        )
        if exercise.status == ExerciseStatus.DONE:
            raise PermissionDenied(f'Задание {exercise_id} уже сдано')
        if not exercise.is_hint_number_valid(hint_number=number):
            raise NotFound(f'Подсказка {number} не найдена')
        with transaction.atomic():
            hint = exercise.pick_hint(hint_number=number)
            exercise.save()
        return Response(data={'hint': hint, 'exercise': self.serializer(exercise).data})


class ExerciseSolveView(AbstractExercisePostView):
    """
    Проверяем ответ на задание. Кэшируем результат на случай обрыва соединения.
    Я не хотел, чтобы response_cache попадал куда-либо дальше, поэтому для целостности транзакция вызывается здесь.
    """

    validator = ExerciseSolveValidation

    def _post(self, request_id: str, exercise_id: str, answer: str) -> HttpResponse:
        self.validate_competition_state()
        team_id = ApplicationContext.team_id.get()
        competition_id = ApplicationContext.competition_id.get()
        exercise = self.get_object_or_404(
            Exercise,
            not_found_message=f'Задание {exercise_id} не найдено',
            competition=competition_id,
            team=team_id,
            id=exercise_id
        )
        response_cache = ResponseCache.objects.filter(request_id=request_id).first()
        if response_cache:
            content = {
                'success': response_cache.success,
                'exercise': self.serializer(exercise).data
            }
            return Response(data=content)

        if exercise.status == ExerciseStatus.DONE:
            raise PermissionDenied(f'Задание {exercise_id} уже сдано')

        with transaction.atomic():
            success = exercise.attempt(answer=answer)
            exercise.save()
            ResponseCache.objects.create(request_id=request_id, success=success)

        return Response(data={'success': success, 'exercise': ExerciseSerializer(exercise).data})
