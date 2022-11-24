from rest_framework import serializers

from ..models import Competition


class CompetitionSerializer(serializers.ModelSerializer):
    id = serializers.CharField()
    countdown = serializers.CharField()
    end_time = serializers.CharField()
    time_left = serializers.CharField()

    class Meta:
        model = Competition
        fields = ('id', 'name', 'start_time', 'end_time', 'countdown', 'time_left', 'status')
