import json
import uuid

from http import HTTPStatus
from datetime import timedelta
from django.test import TestCase
from django.utils import timezone

from ..models import Team, Competition
from ..services import CompetitionInit


class TestCompetition(TestCase):
    """
    Если распараллеливать тесты, желательно для каждого теста использовать разные команды.
    """
    team_id = str(uuid.uuid4())
    team_login = 'test_team'
    team_password = '12345'

    @classmethod
    def setUpTestData(cls):
        Team.objects.create(
            id=cls.team_id,
            login='test_team',
            name=cls.team_login,
            password=cls.team_password
        )

    def get_token(self):
        response = self.client.post(
            path='/api/authorize',
            data={'login': self.team_login, 'password': self.team_password},
            content_type='application/json'
        )
        assert response.status_code == HTTPStatus.OK
        data = json.loads(response.content)
        token = data['auth_token']
        return f'Bearer {token}'

    def get_competition_info(self):
        token = self.get_token()
        return self.client.get(
            path='/api/competition',
            HTTP_Authorization=token
        )

    def test_no_competition(self):
        response = self.get_competition_info()
        assert response.status_code == HTTPStatus.NOT_FOUND
        data = json.loads(response.content)
        assert data['detail'] == 'Соревнование не найдено'

    def test_not_started_competition(self):
        competition_id = str(uuid.uuid4())
        start_time = timezone.now() + timedelta(hours=1)
        competition = Competition.objects.create(
            id=competition_id,
            name='Не начатое соревнование',
            start_time=start_time
        )
        competition.teams.add(self.team_id)
        response = self.get_competition_info()
        assert response.status_code == HTTPStatus.OK
        data = json.loads(response.content)
        assert data['id'] == competition_id
        assert data['name'] == 'Не начатое соревнование'
        assert '0:59:5' in data['countdown']
        assert data['time_left'] == '5:00:00'
        assert data['status'] == 'Не начато'
        competition.delete()

    def test_in_progress_competition(self):
        competition_id = str(uuid.uuid4())
        start_time = timezone.now() - timedelta(hours=1)
        competition = Competition.objects.create(
            id=competition_id,
            name='Соревнование в процессе',
            start_time=start_time
        )
        competition.teams.add(self.team_id)
        CompetitionInit.initialize_competition(competition)
        response = self.get_competition_info()
        assert response.status_code == HTTPStatus.OK
        data = json.loads(response.content)
        assert data['id'] == competition_id
        assert data['name'] == 'Соревнование в процессе'
        assert data['countdown'] == '0:00:00'
        assert '3:59:5' in data['time_left']
        assert data['status'] == 'В процессе'
        competition.delete()

    def test_completed_competition(self):
        competition_id = str(uuid.uuid4())
        start_time = timezone.now() - timedelta(hours=10)
        competition = Competition.objects.create(
            id=competition_id,
            name='Завершенное соревнование',
            start_time=start_time
        )
        competition.teams.add(self.team_id)
        CompetitionInit.initialize_competition(competition)
        response = self.get_competition_info()
        assert response.status_code == HTTPStatus.OK
        data = json.loads(response.content)
        assert data['id'] == competition_id
        assert data['name'] == 'Завершенное соревнование'
        assert data['countdown'] == '0:00:00'
        assert data['time_left'] == '0:00:00'
        assert data['status'] == 'Завершено'
        competition.delete()

    def test_completed_in_progress_and_not_started_competition(self):
        competition_data = [
            {
                'id': str(uuid.uuid4()),
                'name': 'Завершенное соревнование',
                'start_time': timezone.now() - timedelta(hours=10)
            },
            {
                'id': str(uuid.uuid4()),
                'name': 'Текущее соревнование',
                'start_time': timezone.now() - timedelta(hours=1)
            },
            {
                'id': str(uuid.uuid4()),
                'name': 'Будущее соревнование',
                'start_time': timezone.now() + timedelta(hours=10)
            },
        ]
        competitions = []
        for data in competition_data:
            competition = Competition.objects.create(**data)
            competition.teams.add(self.team_id)
            competitions.append(competition)
            CompetitionInit.initialize_competition(competition)

        current_competition = competition_data[1]

        response = self.get_competition_info()
        assert response.status_code == HTTPStatus.OK
        data = json.loads(response.content)

        assert data['id'] == current_competition['id']
        assert data['name'] == 'Текущее соревнование'
        assert data['countdown'] == '0:00:00'
        assert data['status'] == 'В процессе'

        for competition in competitions:
            competition.delete()

    def test_completed_and_not_started_competition(self):
        competition_data = [
            {
                'id': str(uuid.uuid4()),
                'name': 'Завершенное соревнование',
                'start_time': timezone.now() - timedelta(hours=10)
            },
            {
                'id': str(uuid.uuid4()),
                'name': 'Будущее соревнование',
                'start_time': timezone.now() + timedelta(hours=10)
            },
        ]
        competitions = []
        for data in competition_data:
            competition = Competition.objects.create(**data)
            competition.teams.add(self.team_id)
            competitions.append(competition)

        current_competition = competition_data[1]

        response = self.get_competition_info()
        assert response.status_code == HTTPStatus.OK
        data = json.loads(response.content)

        assert data['id'] == current_competition['id']
        assert data['name'] == 'Будущее соревнование'
        assert '9:59:59' in data['countdown']
        assert data['time_left'] == '5:00:00'
        assert data['status'] == 'Не начато'

        for competition in competitions:
            competition.delete()
