from rest_framework.response import Response

from django.core.handlers.wsgi import WSGIRequest
from django.http.response import HttpResponse

from .abstract_api_view import AbstractAPIView

from ..application_context import ApplicationContext
from ..models import Competition
from ..serializers import CompetitionSerializer


class CompetitionView(AbstractAPIView):
    http_method_names = ['get']
    serializer = CompetitionSerializer

    def get(self, request: WSGIRequest) -> HttpResponse:
        competition_id = ApplicationContext.competition_id.get()
        competition = self.get_object_or_404(Competition, 'Соревнование не найдено', pk=competition_id)
        return Response(self.serializer(competition).data)
