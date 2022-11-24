from django.core.management.base import BaseCommand

from django.utils import timezone
from datetime import timedelta

from ...application_context import ApplicationContext
from ...models import Competition, Exercise
from ...services import CompetitionInit


class Command(BaseCommand):
    """
    Команда для инициализации турнира, указанного в фикстуре.
    (можно будет переделать передачу id соревнования через options)
    """
    @staticmethod
    def solve_exercise(exercise: Exercise, answer: str):
        exercise.attempt(answer)
        exercise.save()
        
    @staticmethod
    def pick_hint(exercise: Exercise, hint_number: int):
        exercise.pick_hint(hint_number=hint_number)
        exercise.save()

    def handle(self, **options):
        competition = Competition.objects.get(pk="c67c6b5c-ed3e-41ba-9f2e-d0a6fa4c7cf2")
        competition.start_time = timezone.now() - timedelta(hours=1)
        competition.save()
        CompetitionInit.initialize_competition(competition)

        teams = competition.teams.all()

        ApplicationContext.team_id.set(teams[0])
        ApplicationContext.competition_id.set("c67c6b5c-ed3e-41ba-9f2e-d0a6fa4c7cf2")
        exercises = Exercise.objects.all_team_exercises(teams[0].id)

        self.solve_exercise(exercises[0], '42')
        self.solve_exercise(exercises[1], 'Водопровод')
        self.solve_exercise(exercises[2], 'Календарь')

        ApplicationContext.team_id.set(teams[1])
        exercises = Exercise.objects.all_team_exercises(teams[1].id)
        self.solve_exercise(exercises[0], '42')
        self.pick_hint(exercises[0], 0)
        self.solve_exercise(exercises[1], 'wrong')

        ApplicationContext.team_id.set(teams[2])
        exercises = Exercise.objects.all_team_exercises(teams[2].id)
        self.solve_exercise(exercises[0], 'wrong')
        self.pick_hint(exercises[0], 0)
        self.pick_hint(exercises[0], 1)
        self.pick_hint(exercises[0], 2)
        self.solve_exercise(exercises[1], 'wrong')
        self.pick_hint(exercises[0], 0)
