import json
import uuid

from http import HTTPStatus
from datetime import timedelta
from django.test import TestCase
from django.utils import timezone

from ..models import Team, Competition, TaskDescription
from ..services import CompetitionInit


class TestLeaderboard(TestCase):
    teams = [
        {
            'id': str(uuid.uuid4()),
            'login': 'test_team',
            'name': '1 Тестовая команда',
            'password': '12345'
        },
        {
            'id': str(uuid.uuid4()),
            'login': 'second_team',
            'name': '2 Вторая команда',
            'password': 'qwerty'
        },
        {
            'id': str(uuid.uuid4()),
            'login': 'third_team',
            'name': '3 Третья команда',
            'password': 'qwerty12345'
        },
    ]

    tasks_descriptions = [
        {
            'id': str(uuid.uuid4()),
            'name': 'Тестовое задание 1',
            'coordinates': ['66.666666', '33.333333'],
            'description': 'Описание тестового задания 1',
            'answer': 'Ответ 1',
            'hints': ['Подсказка 1.0', 'Подсказка 1.1', 'Подсказка 1.2']
        },
        {
            'id': str(uuid.uuid4()),
            'name': 'Тестовое задание 2',
            'coordinates': ['11.111111', '44.444444'],
            'description': 'Описание тестового задания 2',
            'answer': 'Ответ 2',
            'hints': ['Подсказка 2.0', 'Подсказка 2.1', 'Подсказка 2.2']
        },
    ]

    @classmethod
    def setUpTestData(cls):
        for team in cls.teams:
            Team.objects.create(**team)
        for description in cls.tasks_descriptions:
            TaskDescription.objects.create(**description)

    def setup_competition(self, start_time=timezone.now() - timedelta(hours=1)):
        competition = Competition.objects.create(
            name='Тестовое соревнование',
            start_time=start_time
        )
        for team in self.teams:
            competition.teams.add(team['id'])
        for task in self.tasks_descriptions:
            competition.tasks.add(task['id'])
        CompetitionInit.initialize_competition(competition)
        return competition

    def get_token(self, login: str, password: str) -> str:
        response = self.client.post(
            path='/api/authorize',
            data={'login': login, 'password': password},
            content_type='application/json'
        )
        assert response.status_code == HTTPStatus.OK
        data = json.loads(response.content)
        token = data['auth_token']
        return f'Bearer {token}'

    def get_exercise_id(self, token: str, task: dict):
        response = self.client.get(
            path='/api/exercise_manager/all_exercises',
            HTTP_Authorization=token
        )
        assert response.status_code == HTTPStatus.OK
        exercises = json.loads(response.content)
        exercise = next(exercise for exercise in exercises if exercise['name'] == task['name'])
        return exercise['id']

    def pick_hint(self, team: dict, task: dict, hint_number: int):
        token = self.get_token(login=team['login'], password=team['password'])
        exercise_id = self.get_exercise_id(token=token, task=task)
        response = self.client.post(
            path='/api/exercise_manager/pick_hint',
            HTTP_Authorization=token,
            data={'exercise_id': exercise_id, 'number': hint_number},
            content_type='application/json'
        )
        assert response.status_code == HTTPStatus.OK
        data = json.loads(response.content)
        assert data['hint'] is not None

    def get_leaderboard(self) -> dict:
        token = self.get_token(login=self.teams[0]['login'], password=self.teams[0]['password'])
        response = self.client.get(
            path='/api/leaderboard',
            HTTP_Authorization=token
        )
        assert response.status_code == HTTPStatus.OK
        return json.loads(response.content)

    def solve(self, team: dict, task: dict, success: bool):
        token = self.get_token(login=team['login'], password=team['password'])
        exercise_id = self.get_exercise_id(token=token, task=task)
        answer = task['answer'] if success else 'wrong answer'
        response = self.client.post(
            path='/api/exercise_manager/solve',
            HTTP_Authorization=token,
            data={'request_id': str(uuid.uuid4()), 'exercise_id': exercise_id, 'answer': answer},
            content_type='application/json'
        )
        assert response.status_code == HTTPStatus.OK
        data = json.loads(response.content)
        assert data['success'] is success

    def test_leaderboard_competition_not_found(self):
        token = self.get_token(login=self.teams[0]['login'], password=self.teams[0]['password'])
        response = self.client.get(
            path='/api/leaderboard',
            HTTP_Authorization=token
        )
        assert response.status_code == HTTPStatus.NOT_FOUND
        data = json.loads(response.content)
        assert data['detail'] == 'Соревнование не найдено'

    def test_leaderboard_competition_not_started(self):
        competition = self.setup_competition(timezone.now() + timedelta(hours=1))
        token = self.get_token(login=self.teams[0]['login'], password=self.teams[0]['password'])
        response = self.client.get(
            path='/api/leaderboard',
            HTTP_Authorization=token
        )
        assert response.status_code == HTTPStatus.FORBIDDEN
        data = json.loads(response.content)
        assert data['detail'] == 'Соревнование еще не начато, во избежание спойлеров о том, сколько команд ' \
                                  'участвует и сколько заданий в соревновании, мы не можем показать вам' \
                                  ' таблицу лидеров.'

        competition.delete()

    def test_leaderboard_meta(self):
        assertion_headers = [
            {
                'col_name': 'Текущее место команды',
                'property_name': 'position',
                'value_type': 'integer',
                'is_visible': True
            },
            {
                'col_name': 'Идентификатор команды',
                'property_name': 'team_id',
                'value_type': 'str',
                'is_visible': False
            },
            {
                'col_name': 'Название команды',
                'property_name': 'team_name',
                'value_type': 'str',
                'is_visible': True
            },
            {
                'col_name': 'Тестовое задание 1',
                'property_name': 'exercise_1',
                'value_type': 'datetime',
                'is_visible': True
            },
            {
                'col_name': 'Тестовое задание 2',
                'property_name': 'exercise_2',
                'value_type': 'datetime',
                'is_visible': True
            },
            {
                'col_name': 'Количество сданных заданий',
                'property_name': 'completed_exercises_count',
                'value_type': 'integer',
                'is_visible': True
            },
            {
                'col_name': 'Суммарное штрафное время',
                'property_name': 'total_penalty_time',
                'value_type': 'timedelta',
                'is_visible': True
            }
        ]
        competition = self.setup_competition()

        leaderboard = self.get_leaderboard()
        meta = leaderboard['meta']
        assert meta['col_count'] == 7
        assert meta['row_count'] == 3
        for number, header in enumerate(meta['column_headers']):
            for key, value in header.items():
                assert value == assertion_headers[number][key]

        competition.delete()

        competition = Competition.objects.create(
            name='Тестовое соревнование',
            start_time=timezone.now() - timedelta(hours=1)
        )
        for team in self.teams:
            competition.teams.add(team['id'])
        for task in self.tasks_descriptions:
            competition.tasks.add(task['id'])
        team = Team.objects.create(login='login', password='password')
        competition.teams.add(team.id)
        task = TaskDescription.objects.create(
                name='Тестовое задание 3',
                description='Описание тестового задания 3',
                coordinates=['11.111111', '44.444444'],
                answer='Ответ 3',
                hints=['1', '2', '3']
        )
        competition.tasks.add(task.id)
        CompetitionInit.initialize_competition(competition)

        assertion_headers = [
            {
                'col_name': 'Текущее место команды',
                'property_name': 'position',
                'value_type': 'integer',
                'is_visible': True
            },
            {
                'col_name': 'Идентификатор команды',
                'property_name': 'team_id',
                'value_type': 'str',
                'is_visible': False
            },
            {
                'col_name': 'Название команды',
                'property_name': 'team_name',
                'value_type': 'str',
                'is_visible': True
            },
            {
                'col_name': 'Тестовое задание 1',
                'property_name': 'exercise_1',
                'value_type': 'datetime',
                'is_visible': True
            },
            {
                'col_name': 'Тестовое задание 2',
                'property_name': 'exercise_2',
                'value_type': 'datetime',
                'is_visible': True
            },
            {
                'col_name': 'Тестовое задание 3',
                'property_name': 'exercise_3',
                'value_type': 'datetime',
                'is_visible': True
            },
            {
                'col_name': 'Количество сданных заданий',
                'property_name': 'completed_exercises_count',
                'value_type': 'integer',
                'is_visible': True
            },
            {
                'col_name': 'Суммарное штрафное время',
                'property_name': 'total_penalty_time',
                'value_type': 'timedelta',
                'is_visible': True
            }
        ]

        leaderboard = self.get_leaderboard()
        meta = leaderboard['meta']
        assert meta['col_count'] == 8
        assert meta['row_count'] == 4
        for number, header in enumerate(meta['column_headers']):
            for key, value in header.items():
                assert value == assertion_headers[number][key]

        competition.delete()

    def test_leaderboard_highlights(self):
        competition = self.setup_competition()

        assertion_highlights = [
            {'location': {'type': 'cell', 'position': 1, 'column': 'team_name'}, 'highlight': 'zero_points'},
            {'location': {'type': 'cell', 'position': 2, 'column': 'team_name'}, 'highlight': 'zero_points'},
            {'location': {'type': 'cell', 'position': 3, 'column': 'team_name'}, 'highlight': 'zero_points'},
        ]
        leaderboard = self.get_leaderboard()
        highlights = leaderboard['highlights']
        for number, highlight in enumerate(highlights):
            for key, value in highlight.items():
                assert value == assertion_highlights[number][key]

        assertion_highlights.pop(0)
        self.solve(self.teams[0], self.tasks_descriptions[0], success=True)
        leaderboard = self.get_leaderboard()
        highlights = leaderboard['highlights']
        for number, highlight in enumerate(highlights):
            for key, value in highlight.items():
                assert value == assertion_highlights[number][key]

        self.solve(self.teams[1], self.tasks_descriptions[0], success=True)
        self.solve(self.teams[2], self.tasks_descriptions[0], success=True)
        leaderboard = self.get_leaderboard()
        assert len(leaderboard['highlights']) == 0
        competition.delete()

    def test_leaderboard_penalty(self):
        competition = self.setup_competition()

        leaderboard = self.get_leaderboard()
        record = next(record for record in leaderboard['records'] if record['team_id'] == self.teams[0]['id'])
        assert record['position'] == 1
        assert record['total_penalty_time'] == '0:00:00'

        self.pick_hint(self.teams[0], self.tasks_descriptions[0], 0)
        leaderboard = self.get_leaderboard()
        record = next(record for record in leaderboard['records'] if record['team_id'] == self.teams[0]['id'])
        assert record['position'] == 3
        assert record['total_penalty_time'] == '0:15:00'

        self.pick_hint(self.teams[0], self.tasks_descriptions[0], 1)
        leaderboard = self.get_leaderboard()
        record = next(record for record in leaderboard['records'] if record['team_id'] == self.teams[0]['id'])
        assert record['position'] == 3
        assert record['total_penalty_time'] == '0:30:00'

        self.solve(self.teams[0], self.tasks_descriptions[0], success=False)
        leaderboard = self.get_leaderboard()
        record = next(record for record in leaderboard['records'] if record['team_id'] == self.teams[0]['id'])
        assert record['position'] == 3
        assert record['total_penalty_time'] == '1:00:00'

        self.solve(self.teams[0], self.tasks_descriptions[0], success=False)
        leaderboard = self.get_leaderboard()
        record = next(record for record in leaderboard['records'] if record['team_id'] == self.teams[0]['id'])
        assert record['position'] == 3
        assert record['total_penalty_time'] == '1:30:00'

        competition.delete()

    def test_leaderboard_sort(self):
        competition = self.setup_competition()
        leaderboard = self.get_leaderboard()
        for i in range(3):
            assert leaderboard['records'][i]['team_id'] == self.teams[i]['id']
            assert leaderboard['records'][i]['team_name'] == self.teams[i]['name']

        self.solve(self.teams[2], self.tasks_descriptions[0], True)
        leaderboard = self.get_leaderboard()
        assert leaderboard['records'][0]['team_name'] == '3 Третья команда'
        assert leaderboard['records'][1]['team_name'] == '1 Тестовая команда'
        assert leaderboard['records'][2]['team_name'] == '2 Вторая команда'

        self.solve(self.teams[1], self.tasks_descriptions[0], True)
        leaderboard = self.get_leaderboard()
        assert leaderboard['records'][0]['team_name'] == '2 Вторая команда'
        assert leaderboard['records'][1]['team_name'] == '3 Третья команда'
        assert leaderboard['records'][2]['team_name'] == '1 Тестовая команда'

        self.solve(self.teams[1], self.tasks_descriptions[1], False)
        leaderboard = self.get_leaderboard()
        assert leaderboard['records'][0]['team_name'] == '3 Третья команда'
        assert leaderboard['records'][1]['team_name'] == '2 Вторая команда'
        assert leaderboard['records'][2]['team_name'] == '1 Тестовая команда'

        self.solve(self.teams[0], self.tasks_descriptions[0], True)
        self.solve(self.teams[0], self.tasks_descriptions[1], True)
        leaderboard = self.get_leaderboard()
        assert leaderboard['records'][0]['team_name'] == '1 Тестовая команда'
        assert leaderboard['records'][1]['team_name'] == '3 Третья команда'
        assert leaderboard['records'][2]['team_name'] == '2 Вторая команда'

        competition.delete()

    def test_leaderboard_records(self):
        competition = self.setup_competition()

        assertion_leaderboard_record = {
            'position': 2,
            'team_id': self.teams[1]['id'],
            'team_name': '2 Вторая команда',
            'exercise_1': None,
            'exercise_2': None,
            'completed_exercise_count': 0,
            'total_penalty_time': '0:00:00'
        }
        leaderboard = self.get_leaderboard()
        record = next(record for record in leaderboard['records'] if record['team_id'] == self.teams[1]['id'])
        for key, value in record.items():
            assert value == assertion_leaderboard_record[key]

        assertion_leaderboard_record['position'] = 1
        assertion_leaderboard_record.pop('exercise_1')
        assertion_leaderboard_record['completed_exercise_count'] = 1
        self.solve(self.teams[1], self.tasks_descriptions[0], True)
        leaderboard = self.get_leaderboard()
        record = next(record for record in leaderboard['records'] if record['team_id'] == self.teams[1]['id'])
        for key, value in assertion_leaderboard_record.items():
            assert value == record[key]
        assert record['exercise_1'] is not None

        assertion_leaderboard_record.pop('exercise_2')
        assertion_leaderboard_record['completed_exercise_count'] = 2
        self.solve(self.teams[1], self.tasks_descriptions[1], True)
        leaderboard = self.get_leaderboard()
        record = next(record for record in leaderboard['records'] if record['team_id'] == self.teams[1]['id'])
        for key, value in assertion_leaderboard_record.items():
            assert value == record[key]
        assert record['exercise_1'] is not None
        assert record['exercise_2'] is not None

        competition.delete()
