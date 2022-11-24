from django.contrib import admin
from django.http import HttpResponseRedirect
from django_better_admin_arrayfield.admin.mixins import DynamicArrayMixin

from .forms import TeamForm
from .models import Team, TaskDescription, Competition
from .models.competition import CompetitionStatus
from .services import CompetitionInit


@admin.register(Team)
class MyModelAdmin(admin.ModelAdmin, DynamicArrayMixin):
    form = TeamForm


@admin.register(TaskDescription)
class MyModelAdmin(admin.ModelAdmin, DynamicArrayMixin):
    pass


@admin.register(Competition)
class CompetitionModelAdmin(admin.ModelAdmin, DynamicArrayMixin):
    """
    Модель для работы с сущностью "Соревнование" в админке.
    Подразумевается, что после создания и сохранения соревнования, необходимо инициализировать объекты для работы.
    После инициализации не разрешается менять команды и задания (для упрощения).
    После начала задания, запрещается его изменять.
    Еще можно было бы сделать кнопку "Отменить соревнование", чтобы администратор мог вносить изменения.
    """
    readonly_fields = ['initialized']
    change_form_template = "admin/competition_change.html"

    def get_readonly_fields(self, request, obj=None):
        if not obj:
            return []
        # После начала соревнования запрещаем его менять.
        if obj.status != CompetitionStatus.NOT_STARTED:
            return ['name', 'start_time', 'initialized', 'teams', 'tasks']
        # После инициализации соревнования, запрещаем менять команды и задания.
        elif getattr(obj, 'initialized', False):
            return ['initialized', 'teams', 'tasks']
        return self.readonly_fields

    def response_change(self, request, obj):
        if "_initialize" in request.POST:
            if obj.initialized:
                self.message_user(request, "Соревнование уже было инициализировано")
                return HttpResponseRedirect(".")
            CompetitionInit.initialize_competition(obj)
            self.message_user(request, "Соревнование успешно инициализировано")
            return HttpResponseRedirect(".")
        return super().response_change(request, obj)
