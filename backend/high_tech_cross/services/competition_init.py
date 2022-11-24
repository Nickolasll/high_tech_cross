from django.db import transaction

from ..models import Competition, Exercise


class CompetitionInit:
    """
    Действия, которые порождают сразу несколько объектов я решил делать не поведением самого объекта, а через менеджера.
    Также здесь в дальнейшем можно реализовать действие по отмене турнира.
    """

    @classmethod
    def initialize_competition(cls, competition: Competition):
        """
        Создает необходимые для функционирования соревнования сущности:
        - Исполнения заданий для каждой из команд в соревновании
        - Записи таблицы лидеров
        :param competition:
        :return:
        """
        if competition.initialized:
            return

        teams = competition.teams.all()
        tasks = competition.tasks.all()

        competition.initialized = True

        with transaction.atomic():
            competition.save()

            for team in teams:
                for task in tasks:
                    Exercise.objects.create(team=team, competition=competition, task_description=task)
