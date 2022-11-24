from django.core.handlers.wsgi import WSGIRequest
from django.http.response import HttpResponse

from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from .abstract_api_view import AbstractAPIView
from ..models.competition import CompetitionStatus
from ..services import Leaderboard
from ..application_context import ApplicationContext
from ..models import Competition


class LeaderboardView(AbstractAPIView):
    http_method_names = ['get']

    def get(self, request: WSGIRequest) -> HttpResponse:
        competition_id = ApplicationContext.competition_id.get()
        competition = self.get_object_or_404(Competition, 'Соревнование не найдено', pk=competition_id)
        if competition.status == CompetitionStatus.NOT_STARTED:
            message = 'Соревнование еще не начато, во избежание спойлеров о том, сколько команд участвует ' \
                      'и сколько заданий в соревновании, мы не можем показать вам таблицу лидеров.'
            raise PermissionDenied(message)

        return Response(data=Leaderboard.get_table())
