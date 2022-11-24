from rest_framework import serializers

from ..models import Team


class TeamSerializer(serializers.ModelSerializer):
    login = serializers.CharField(max_length=30)

    class Meta:
        model = Team
        fields = ('login', 'password')
