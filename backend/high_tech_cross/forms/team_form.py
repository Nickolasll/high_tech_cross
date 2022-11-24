from django import forms

from ..models import Team


class TeamForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(render_value=True))

    class Meta:
        model = Team
        fields = ['login', 'name', 'password']
