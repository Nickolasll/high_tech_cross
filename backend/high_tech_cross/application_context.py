from contextvars import ContextVar
from typing import Optional


class ApplicationContext:
    """
    Контекст приложения, в котором мы передаем team_id и competition_id из middleware в обработчики запросов view
    """

    team_id: ContextVar[Optional[str]] = ContextVar('team_id', default=None)
    competition_id: ContextVar[Optional[str]] = ContextVar('competition_id', default=None)
