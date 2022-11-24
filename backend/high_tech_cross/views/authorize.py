from http import HTTPStatus

from rest_framework.response import Response

from .abstract_api_view import AbstractAPIView

from ..serializers import TeamSerializer
from ..services import Authorization


class AuthorizationView(AbstractAPIView):
    http_method_names = ['post']
    validator = TeamSerializer

    def _post(self, login: str, password: str):
        result = Authorization.authorize(login=login, password=password)
        if not result:
            return Response({'message': 'Неправильный логин или пароль.'}, status=HTTPStatus.NOT_FOUND)

        return Response(result)
