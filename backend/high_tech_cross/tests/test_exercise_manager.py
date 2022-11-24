import json
import uuid

from http import HTTPStatus
from datetime import timedelta
from django.test import TestCase
from django.utils import timezone

from ..models import Team, Competition, TaskDescription, Rule
from ..services import CompetitionInit


class TestExerciseManager(TestCase):
    team_id = '90354b47-a0e4-46ec-b61f-e6efb494e36d'
    team_login = 'test_team'
    team_password = '12345'
    task_description_ids = [
        '28d9a800-02a7-4a7c-89ad-d11c1befc104',
        '0dbf8c1e-d77b-4ec4-b0a9-68ad01305188',
    ]

    @classmethod
    def setUpTestData(cls):
        Team.objects.create(
            id=cls.team_id,
            login='test_team',
            name=cls.team_login,
            password=cls.team_password
        )
        TaskDescription.objects.create(
            id=cls.task_description_ids[0],
            name='Тестовое задание 1',
            coordinates=['66.666666', '33.333333'],
            description='Описание тестового задания 1',
            answer='Ответ 1',
            hints=['Подсказка 1.0', 'Подсказка 1.1', 'Подсказка 1.2']
        )
        TaskDescription.objects.create(
            id=cls.task_description_ids[1],
            name='Тестовое задание 2',
            coordinates=['11.111111', '44.444444'],
            description='Описание тестового задания 2',
            answer='Ответ 2',
            hints=['Подсказка 2.0', 'Подсказка 2.1', 'Подсказка 2.2']
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

    def get_all_exercises(self):
        token = self.get_token()
        response = self.client.get(
            path='/api/exercise_manager/all_exercises',
            HTTP_Authorization=token
        )
        assert response.status_code == HTTPStatus.OK
        return json.loads(response.content)

    def get_one_exercise(self, exercise_id):
        token = self.get_token()
        return self.client.get(
            path=f'/api/exercise_manager/exercise/{exercise_id}',
            HTTP_Authorization=token
        )

    def solve(self, request_id, exercise_id, answer):
        token = self.get_token()
        response = self.client.post(
            path='/api/exercise_manager/solve',
            HTTP_Authorization=token,
            data={'request_id': request_id, 'exercise_id': exercise_id, 'answer': answer},
            content_type='application/json'
        )
        assert response.status_code == HTTPStatus.OK
        return json.loads(response.content)

    def get_hint(self, exercise_id, hint_number):
        token = self.get_token()
        return self.client.post(
            path='/api/exercise_manager/pick_hint',
            HTTP_Authorization=token,
            data={'exercise_id': exercise_id, 'number': hint_number},
            content_type='application/json'
        )

    def init_full_competition(self, start_time):
        competition = Competition.objects.create(
            name='Тестовое соревнование',
            start_time=start_time
        )
        competition.teams.add(self.team_id)
        competition.tasks.add(self.task_description_ids[0])
        competition.tasks.add(self.task_description_ids[1])
        CompetitionInit.initialize_competition(competition)
        return competition

    def test_get_all_success(self):
        competition = self.init_full_competition(timezone.now() - timedelta(hours=1))
        exercises = self.get_all_exercises()
        assertion_data = [
            {
                'name': 'Тестовое задание 1',
                'description': 'Описание тестового задания 1',
                'coordinates': ['66.666666', '33.333333'],
                'hints': [],
                'max_hints': 3,
                'status': 'Не начато',
                'completed_at': None,
                'used_hints_count': 0,
                'is_hint_available': True,
                'wrong_attempts': 0,
                'penalty_time': '0:00:00'
            },
            {
                'name': 'Тестовое задание 2',
                'description': 'Описание тестового задания 2',
                'coordinates': ['11.111111', '44.444444'],
                'hints': [],
                'max_hints': 3,
                'status': 'Не начато',
                'completed_at': None,
                'used_hints_count': 0,
                'is_hint_available': True,
                'wrong_attempts': 0,
                'penalty_time': '0:00:00'
            }
        ]
        for index, snapshot in enumerate(exercises):
            for key, value in snapshot.items():
                if key == 'id':
                    continue
                assert assertion_data[index][key] == value
        competition.delete()

    def test_get_all_no_competition(self):
        token = self.get_token()
        response = self.client.get(
            path='/api/exercise_manager/all_exercises',
            HTTP_Authorization=token
        )
        assert response.status_code == HTTPStatus.NOT_FOUND
        data = json.loads(response.content)
        assert data['detail'] == 'Соревнование не найдено'

    def test_get_all_not_started(self):
        competition = Competition.objects.create(
            name='Не начатое соревнование',
            start_time=timezone.now() + timedelta(hours=1)
        )
        competition.teams.add(self.team_id)
        token = self.get_token()
        response = self.client.get(
            path='/api/exercise_manager/all_exercises',
            HTTP_Authorization=token
        )
        assert response.status_code == HTTPStatus.FORBIDDEN
        data = json.loads(response.content)
        assert data['detail'] == 'Соревнование еще не начато, во избежание спойлеров вы не ' \
                                 'можете ни смотреть, ни работать с заданиями'
        competition.delete()

    def test_get_one_success(self):
        competition = self.init_full_competition(timezone.now() - timedelta(hours=1))
        exercises = self.get_all_exercises()
        exercise_id = exercises[0]['id']
        response = self.get_one_exercise(exercise_id)
        assert response.status_code == HTTPStatus.OK
        data = json.loads(response.content)
        assertion_data = {
            'name': 'Тестовое задание 1',
            'description': 'Описание тестового задания 1',
            'coordinates': ['66.666666', '33.333333'],
            'hints': [],
            'max_hints': 3,
            'status': 'Не начато',
            'completed_at': None,
            'used_hints_count': 0,
            'is_hint_available': True,
            'wrong_attempts': 0,
            'penalty_time': '0:00:00'
        }
        for key, value in data.items():
            if key == 'id':
                continue
            assert assertion_data[key] == value
        competition.delete()

    def test_get_one_not_found(self):
        competition = Competition.objects.create(
            name='Тестовое соревнование',
            start_time=timezone.now() - timedelta(hours=1)
        )
        competition.teams.add(self.team_id)
        CompetitionInit.initialize_competition(competition)
        exercise_id = str(uuid.uuid4())
        response = self.get_one_exercise(exercise_id)
        assert response.status_code == HTTPStatus.NOT_FOUND
        data = json.loads(response.content)
        assert data['detail'] == f'Задание {exercise_id} не найдено'
        competition.delete()

    def test_get_hints(self):
        competition = self.init_full_competition(timezone.now() - timedelta(hours=1))
        exercises = self.get_all_exercises()
        hint_number = 3
        for index, exercise in enumerate(exercises):
            hints = []
            for number in range(hint_number):
                hint = f'Подсказка {index + 1}.{number}'
                hints.append(hint)
                used_hints_count = number + 1
                penalty_time = str(Rule.hint_penalty * (number + 1))

                response = self.get_hint(exercise_id=exercise['id'], hint_number=number)
                assert response.status_code == HTTPStatus.OK
                data = json.loads(response.content)
                assert data['hint'] == hint
                assert data['exercise']['hints'] == hints
                assert data['exercise']['status'] == 'Начато'
                assert data['exercise']['used_hints_count'] == used_hints_count
                assert data['exercise']['penalty_time'] == penalty_time
                if number != hint_number - 1:
                    assert data['exercise']['is_hint_available'] is True
                else:
                    assert data['exercise']['is_hint_available'] is False
        competition.delete()

    def test_get_hint_not_found(self):
        competition = self.init_full_competition(timezone.now() - timedelta(hours=1))
        hint_number = 4
        exercises = self.get_all_exercises()
        response = self.get_hint(exercise_id=exercises[0]['id'], hint_number=hint_number)
        assert response.status_code == HTTPStatus.NOT_FOUND
        data = json.loads(response.content)
        assert data['detail'] == f'Подсказка {hint_number} не найдена'
        competition.delete()

    def test_get_hint_over_and_over(self):
        competition = self.init_full_competition(timezone.now() - timedelta(hours=1))
        exercises = self.get_all_exercises()
        hint_number = 1
        hint = f'Подсказка 1.{hint_number}'
        penalty_time = str(Rule.hint_penalty)

        for i in range(10):
            response = self.get_hint(exercise_id=exercises[0]['id'], hint_number=hint_number)
            assert response.status_code == HTTPStatus.OK
            data = json.loads(response.content)
            assert data['hint'] == hint
            assert data['exercise']['hints'] == [hint]
            assert data['exercise']['status'] == 'Начато'
            assert data['exercise']['used_hints_count'] == 1
            assert data['exercise']['penalty_time'] == penalty_time
            assert data['exercise']['is_hint_available'] is True

        hint_2 = f'Подсказка 1.{2}'
        penalty_time = str(Rule.hint_penalty * 2)

        response = self.get_hint(exercise_id=exercises[0]['id'], hint_number=2)
        assert response.status_code == HTTPStatus.OK
        data = json.loads(response.content)
        assert data['hint'] == hint_2
        assert data['exercise']['hints'] == [hint, hint_2]
        assert data['exercise']['status'] == 'Начато'
        assert data['exercise']['used_hints_count'] == 2
        assert data['exercise']['penalty_time'] == penalty_time
        assert data['exercise']['is_hint_available'] is True

        competition.delete()

    def test_get_hint_wrong_format(self):
        competition = self.init_full_competition(timezone.now() - timedelta(hours=1))
        exercises = self.get_all_exercises()
        response = self.get_hint(exercise_id=exercises[0]['id'], hint_number='не число')
        assert response.status_code == HTTPStatus.BAD_REQUEST
        data = json.loads(response.content)
        assert data['number'] == ['A valid integer is required.']
        competition.delete()

    def test_get_hint_completed_exercise(self):
        competition = self.init_full_competition(timezone.now() - timedelta(hours=1))
        exercises = self.get_all_exercises()
        self.solve(request_id=str(uuid.uuid4()), exercise_id=exercises[0]['id'], answer='Ответ 1')
        response = self.get_hint(exercise_id=exercises[0]['id'], hint_number=1)
        assert response.status_code == HTTPStatus.FORBIDDEN
        data = json.loads(response.content)
        assert data['detail'] == f"Задание {exercises[0]['id']} уже сдано"
        competition.delete()

    def test_solve_success(self):
        competition = self.init_full_competition(timezone.now() - timedelta(hours=1))
        exercises = self.get_all_exercises()
        data = self.solve(request_id=str(uuid.uuid4()), exercise_id=exercises[0]['id'], answer='Ответ 1')
        assert data['success'] is True
        assert data['exercise']['status'] == 'Сдано'
        assert data['exercise']['completed_at'] is not None
        assert data['exercise']['penalty_time'] == '0:00:00'
        competition.delete()

    def test_solve_wrong_answer(self):
        competition = self.init_full_competition(timezone.now() - timedelta(hours=1))
        exercises = self.get_all_exercises()
        for i in range(1, 10):
            data = self.solve(request_id=str(uuid.uuid4()), exercise_id=exercises[0]['id'], answer='Неправильно')
            assert data['success'] is False
            assert data['exercise']['status'] == 'Попытка сдачи'
            assert data['exercise']['wrong_attempts'] == i
            assert data['exercise']['penalty_time'] == str(Rule.wrong_attempt_penalty * i)

        competition.delete()

    def test_solve_solved_exercise(self):
        competition = self.init_full_competition(timezone.now() - timedelta(hours=1))
        exercises = self.get_all_exercises()
        self.solve(request_id=str(uuid.uuid4()), exercise_id=exercises[0]['id'], answer='Ответ 1')
        token = self.get_token()
        response = self.client.post(
            path='/api/exercise_manager/solve',
            HTTP_Authorization=token,
            data={'request_id': str(uuid.uuid4()), 'exercise_id': exercises[0]['id'], 'answer': 'Неправильно'},
            content_type='application/json'
        )
        assert response.status_code == HTTPStatus.FORBIDDEN
        data = json.loads(response.content)
        assert data['detail'] == f"Задание {exercises[0]['id']} уже сдано"
        competition.delete()

    def test_solve_completed_competition(self):
        competition = self.init_full_competition(timezone.now() - timedelta(hours=10))
        exercises = self.get_all_exercises()
        token = self.get_token()
        response = self.client.post(
            path='/api/exercise_manager/solve',
            HTTP_Authorization=token,
            data={'request_id': str(uuid.uuid4()), 'exercise_id': exercises[0]['id'], 'answer': 'Ответ 1'},
            content_type='application/json'
        )
        assert response.status_code == HTTPStatus.FORBIDDEN
        data = json.loads(response.content)
        assert data['detail'] == 'Соревнование уже закончилось'
        competition.delete()

    def test_solve_not_started_competition(self):
        competition = self.init_full_competition(timezone.now() - timedelta(hours=1))
        exercises = self.get_all_exercises()
        competition.start_time = timezone.now() + timedelta(hours=10)
        competition.save()
        token = self.get_token()
        response = self.client.post(
            path='/api/exercise_manager/solve',
            HTTP_Authorization=token,
            data={'request_id': str(uuid.uuid4()), 'exercise_id': exercises[0]['id'], 'answer': 'Ответ 1'},
            content_type='application/json'
        )
        assert response.status_code == HTTPStatus.FORBIDDEN
        data = json.loads(response.content)
        assert data['detail'] == 'Соревнование еще не начато, во избежание спойлеров вы не можете ' \
                                 'ни смотреть, ни работать с заданиями'
        competition.delete()

    def test_solve_exercise_not_found(self):
        competition = Competition.objects.create(
            name='Соревнование',
            start_time=timezone.now() - timedelta(hours=1)
        )
        competition.teams.add(self.team_id)
        CompetitionInit.initialize_competition(competition)

        exercise_id = str(uuid.uuid4())
        token = self.get_token()
        response = self.client.post(
            path='/api/exercise_manager/solve',
            HTTP_Authorization=token,
            data={'request_id': str(uuid.uuid4()), 'exercise_id': exercise_id, 'answer': 'Ответ 1'},
            content_type='application/json'
        )
        assert response.status_code == HTTPStatus.NOT_FOUND
        data = json.loads(response.content)
        assert data['detail'] == f'Задание {exercise_id} не найдено'
        competition.delete()

    def test_solve_repeat_connection_error(self):
        competition = self.init_full_competition(timezone.now() - timedelta(hours=1))
        exercises = self.get_all_exercises()
        request_id = str(uuid.uuid4())
        for i in range(10):
            data = self.solve(request_id=request_id, exercise_id=exercises[0]['id'], answer='Неправильно')
            assert data['success'] is False
            assert data['exercise']['status'] == 'Попытка сдачи'
            assert data['exercise']['wrong_attempts'] == 1
            assert data['exercise']['penalty_time'] == str(Rule.wrong_attempt_penalty)
            assert data['exercise']['completed_at'] is None
            assert data['exercise']['is_hint_available'] is True

        request_id = str(uuid.uuid4())
        for i in range(10):
            data = self.solve(request_id=request_id, exercise_id=exercises[0]['id'], answer='Ответ 1')
            assert data['success'] is True
            assert data['exercise']['status'] == 'Сдано'
            assert data['exercise']['wrong_attempts'] == 1
            assert data['exercise']['penalty_time'] == str(Rule.wrong_attempt_penalty)
            assert data['exercise']['completed_at'] is not None
            assert data['exercise']['is_hint_available'] is False

        competition.delete()

    def test_competition_not_initialized(self):
        competition = Competition.objects.create(
            name='Тестовое соревнование',
            start_time=timezone.now() - timedelta(hours=1)
        )
        competition.teams.add(self.team_id)
        competition.tasks.add(self.task_description_ids[0])
        competition.tasks.add(self.task_description_ids[1])
        token = self.get_token()
        response = self.client.get(
            path='/api/exercise_manager/all_exercises',
            HTTP_Authorization=token
        )
        assert response.status_code == HTTPStatus.NOT_FOUND
        data = json.loads(response.content)
        assert data['detail'] == 'Соревнование не найдено'
        competition.delete()
