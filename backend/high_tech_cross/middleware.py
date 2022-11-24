import jwt

from http import HTTPStatus

from django.http import JsonResponse

from .application_context import ApplicationContext
from .config import JWT_SECRET_KEY


class JWTCheckMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # One-time configuration and initialization.

    def __call__(self, request):
        # Code to be executed for each request before the view (and later middleware) are called.

        # Проверка токена осталась здесь, несмотря на то что DRF позволяет использовать authentication_classes для
        # каждого обработчика. Однако, я хотел, чтобы ApplicationContext устанавливался как можно раньше

        if '/api' in request.path and request.path != '/api/authorize':
            token = request.headers.get('Authorization')
            if not token:
                return JsonResponse(data={'detail': 'Token not found'}, status=HTTPStatus.FORBIDDEN)
            try:
                token_data = token.split(' ')
                if token_data[0] != 'Bearer':
                    return JsonResponse(data={'detail': 'Invalid token'}, status=HTTPStatus.FORBIDDEN)
                token_data = jwt.decode(token_data[1], JWT_SECRET_KEY)
            except jwt.ExpiredSignatureError:
                return JsonResponse(data={'detail': 'Token expired'}, status=HTTPStatus.FORBIDDEN)
            except jwt.InvalidTokenError:
                return JsonResponse(data={'detail': 'Invalid token'}, status=HTTPStatus.FORBIDDEN)

            # setup ApplicationContext.
            ApplicationContext.team_id.set(token_data['team_id'])
            ApplicationContext.competition_id.set(token_data['competition_id'])

        response = self.get_response(request)

        # Code to be executed for each request/response after the view is called.
        # Clear ApplicationContext.
        ApplicationContext.team_id.set(None)
        ApplicationContext.competition_id.set(None)

        return response
