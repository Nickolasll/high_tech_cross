from django.urls import path
from .views import AuthorizationView, CompetitionView, ExerciseView, ExerciseHintView, ExerciseSolveView, \
    LeaderboardView

urlpatterns = [
    path('authorize', AuthorizationView.as_view()),
    path('competition', CompetitionView.as_view()),
    path('exercise_manager/all_exercises', ExerciseView.as_view()),
    path('exercise_manager/exercise/<str:exercise_id>', ExerciseView.as_view()),
    path('exercise_manager/pick_hint', ExerciseHintView.as_view()),
    path('exercise_manager/solve', ExerciseSolveView.as_view()),
    path('leaderboard', LeaderboardView.as_view()),
]
