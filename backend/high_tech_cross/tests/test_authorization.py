import json
import uuid
import pytz

from http import HTTPStatus
from datetime import datetime
from django.test import TestCase

from ..models import Team, Competition


class AuthorizationTestCase(TestCase):
    team_id = '90354b47-a0e4-46ec-b61f-e6efb494e36d'
    competition_id = 'b9e09178-5f97-49bc-9da6-753d141e8eab'
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
        new_competition = Competition.objects.create(
            id=cls.competition_id,
            name='Новое соревнование',
        )
        new_competition.teams.add(cls.team_id)
        old_competition = Competition.objects.create(
            id='99b3cb3b-b66d-4d62-b340-420f867e5a89',
            name='Старое соревнование',
            start_time=datetime(year=2000, month=1, day=1, tzinfo=pytz.UTC)
        )
        old_competition.teams.add(cls.team_id)

    def authorize(self, data: dict):
        return self.client.post(
            path='/api/authorize',
            data=data,
            content_type='application/json'
        )

    def test_success_login(self):
        data = {'login': self.team_login, 'password': self.team_password}
        response = self.authorize(data)
        assert response.status_code == HTTPStatus.OK
        data = json.loads(response.content)
        assert data['auth_token'] is not None
        assert data['team_id'] == self.team_id
        assert data['competition_id'] == self.competition_id

    def test_wrong_password(self):
        data = {'login': self.team_login, 'password': 'wrong password'}
        response = self.authorize(data)
        assert response.status_code == HTTPStatus.NOT_FOUND
        data = json.loads(response.content)
        assert data['message'] == 'Неправильный логин или пароль.'

    def test_format(self):
        data = {'login': 123, 'password': 123}
        response = self.authorize(data)
        assert response.status_code == HTTPStatus.NOT_FOUND
        data = json.loads(response.content)
        assert data['message'] == 'Неправильный логин или пароль.'

    def test_not_allowed_method(self):
        response = self.client.get(path='/api/authorize')
        assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED
        data = json.loads(response.content)
        assert data['detail'] == 'Method "GET" not allowed.'

    def test_not_enough_body_params(self):
        data = {'login': self.team_login}
        response = self.authorize(data)
        assert response.status_code == HTTPStatus.BAD_REQUEST
        data = json.loads(response.content)
        assert data['password'] == ['This field is required.']

    def test_overload_body_request(self):
        data = {'login': self.team_login, 'password': self.team_password, 'overload': True}
        response = self.authorize(data)
        assert response.status_code == HTTPStatus.OK
        data = json.loads(response.content)
        assert data['auth_token'] is not None
        assert data['team_id'] == self.team_id
        assert data['competition_id'] == self.competition_id

    def test_team_no_competition(self):
        team_id = str(uuid.uuid4())
        Team.objects.create(
            id=team_id,
            login='test_team_no_competition',
            name='Команда без соревнования',
            password=self.team_password
        )
        response = self.client.post(
            path='/api/authorize',
            data={'login': 'test_team_no_competition', 'password': self.team_password, 'overload': True},
            content_type='application/json'
        )
        assert response.status_code == HTTPStatus.OK
        data = json.loads(response.content)
        assert data['auth_token'] is not None
        assert data['team_id'] == team_id
        assert data['competition_id'] is None

    def test_team_not_found(self):
        data = {'login': 'not found', 'password': 'not found'}
        response = self.authorize(data)
        assert response.status_code == HTTPStatus.NOT_FOUND
        data = json.loads(response.content)
        assert data['message'] == 'Неправильный логин или пароль.'
