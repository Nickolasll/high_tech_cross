from typing import List

from django.contrib.postgres.aggregates import ArrayAgg
from django.db import models
from django.db.models.aggregates import Count, Sum
from django.db.models.expressions import F

from ..application_context import ApplicationContext
from ..models import Competition, Rule


class Leaderboard:

    @staticmethod
    def _prepare_column_headers(competition: Competition) -> List[dict]:
        # Для клиента будет важен порядок столбцов
        headers = [
            {
                'col_name': 'Текущее место команды',
                'property_name': 'position',
                'value_type': 'integer',
                'is_visible': True,
            },
            {
                'col_name': 'Идентификатор команды',
                'property_name': 'team_id',
                'value_type': 'str',
                'is_visible': False,
            },
            {
                'col_name': 'Название команды',
                'property_name': 'team_name',
                'value_type': 'str',
                'is_visible': True,
            },
        ]
        tasks = competition.tasks.all()
        for number, task in enumerate(tasks, start=1):
            headers.append({
                'col_name': task.name if task.name else str(task.id),
                'property_name': f'exercise_{number}',
                'value_type': 'datetime',
                'is_visible': True
            })
        headers.extend([
            {
                'col_name': 'Количество сданных заданий',
                'property_name': 'completed_exercises_count',
                'value_type': 'integer',
                'is_visible': True,
            },
            {
                'col_name': 'Суммарное штрафное время',
                'property_name': 'total_penalty_time',
                'value_type': 'timedelta',
                'is_visible': True,
            },
        ])
        return headers

    @staticmethod
    def _prepare_highlights(records: List[dict]) -> List[dict]:
        """
        Для примера, реализация "подсветки" команд, которые не решили ни одного задания.
        :param records:
        :return:
        """
        highlights = []
        for record in records:
            if record.get('completed_exercise_count', 0) == 0:
                highlights.append({
                    'location': {
                        'type': 'cell',
                        'position': record['position'],
                        'column': 'team_name'
                    },
                    'highlight': 'zero_points'
                })
        return highlights

    @classmethod
    def _get_records(cls, competition: Competition) -> List[dict]:
        """
        Агрегирует таблицу лидеров относительно команд, участвующих в соревновании competition.

        Сортирует по количеству выполненных заданий, штрафному времени и наименованию команды
        (в случае совпадения количества заданий и штрафного времени).

        Возвращает результат в сериализованном виде.
        :param competition:
        :return:
        """
        serialized_records = []
        leaderboard_records = competition.teams.annotate(
            completed_exercises_count=Count('exercise__completed_at'),
            penalty_time=Sum(
                F('exercise__wrong_attempts') * Rule.wrong_attempt_penalty + F('exercise__used_hints__len') *
                Rule.hint_penalty, output_field=models.DurationField()
            ),
            completed_at_results=ArrayAgg('exercise__completed_at'),
            team_id=F('id'),
            team_name=F('name')
        ).order_by('-completed_exercises_count', 'penalty_time', 'name').defer('id', 'name', 'login', 'password')

        for number, record in enumerate(leaderboard_records, start=1):
            serialized_record = {
                'position': number,
                'team_id': str(record.team_id),
                'team_name': record.team_name,
            }

            for task_number, completed_at in enumerate(record.completed_at_results, start=1):
                serialized_record[f'exercise_{task_number}'] = completed_at

            serialized_record.update({
                'completed_exercise_count': record.completed_exercises_count,
                'total_penalty_time': str(record.penalty_time)
            })
            serialized_records.append(serialized_record)

        return serialized_records

    @classmethod
    def get_table(cls) -> dict:

        competition_id = ApplicationContext.competition_id.get()
        competition = Competition.objects.get(pk=competition_id)
        column_headers = cls._prepare_column_headers(competition)
        serialized_records = cls._get_records(competition)
        highlights = cls._prepare_highlights(serialized_records)

        return {
            'meta': {
                'col_count': len(column_headers),
                'row_count': len(serialized_records),
                'column_headers': column_headers,
            },
            'records': serialized_records,
            'highlights': highlights,
        }
