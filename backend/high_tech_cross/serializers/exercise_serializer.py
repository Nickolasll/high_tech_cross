from typing import List

from rest_framework import serializers

from ..models import Exercise


class ExerciseHintValidation(serializers.Serializer):
    exercise_id = serializers.CharField()
    number = serializers.IntegerField()


class ExerciseSolveValidation(serializers.Serializer):
    request_id = serializers.CharField()
    exercise_id = serializers.CharField()
    answer = serializers.CharField()


class ExerciseSerializer(serializers.ModelSerializer):
    id = serializers.CharField()
    status = serializers.CharField()
    name = serializers.SerializerMethodField(method_name='get_name')
    description = serializers.SerializerMethodField(method_name='get_description')
    coordinates = serializers.SerializerMethodField(method_name='get_coordinates')
    used_hints_count = serializers.IntegerField()
    hints = serializers.SerializerMethodField(method_name='get_hints')
    completed_at = serializers.CharField()
    penalty_time = serializers.CharField()
    max_hints = serializers.SerializerMethodField(method_name='get_max_hints')

    class Meta:
        model = Exercise
        fields = (
            'id',
            'status',
            'name',
            'description',
            'coordinates',
            'hints',
            'used_hints_count',
            'is_hint_available',
            'max_hints',
            'completed_at',
            'wrong_attempts',
            'penalty_time',
        )

    def get_name(self, obj: Exercise) -> str:
        return obj.task_description.name

    def get_description(self, obj: Exercise) -> str:
        return obj.task_description.description

    def get_coordinates(self, obj: Exercise) -> list:
        return obj.task_description.coordinates

    def get_hints(self, obj: Exercise) -> List[dict]:
        return [obj.task_description.hints[index] for index in obj.used_hints]

    def get_max_hints(self, obj: Exercise) -> int:
        return obj.task_description.max_hints
