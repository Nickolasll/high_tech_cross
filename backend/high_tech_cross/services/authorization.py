import jwt

from typing import Optional

from django.contrib.auth.hashers import check_password
from django.utils import timezone

from ..config import JWT_SECRET_KEY
from ..models import Team, Rule, Competition


class Authorization:
    """
    Stateless служба авторизации в систему HighTechCross.
    Оперирует логикой по авторизации (а в будущем регистрацией, сменой пароля и т.д.)
    """

    @staticmethod
    def authorize(login: str, password: str) -> Optional[dict]:
        """
        Инкапсулирует логику поиска команды и проверки пароля.
        Для простоты храним пароль в незашифрованном виде.
        :param login: логин команды
        :param password: пароль команды
        :return: None или dict с auth_token, team_id и competition_id
        """
        team = Team.objects.get_by_login(login=login)

        if not team or not check_password(password.lower(), team.password):
            return

        current_time = timezone.now()
        team_id = str(team.id)
        competition_id = Competition.objects.get_nearest_competition_id(current_time=current_time, team_id=team_id)
        payload = {
            'exp': current_time + Rule.competition_duration,
            'iat': current_time,
            'team_id': team_id,
            'competition_id': competition_id
        }
        token = jwt.encode(
            payload,
            JWT_SECRET_KEY,
            algorithm='HS256'
        )
        return {
            'auth_token': token.decode(),
            'team_id': team_id,
            'competition_id': competition_id
        }
