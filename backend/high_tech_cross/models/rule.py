from datetime import timedelta


class Rule:
    """
    Здесь хранятся правила турнира: его длительность, штраф за неправильную попытку и штраф за подсказку.
    В случае необходимости, если правила от турнира к турниру будут меняться - их можно сделать моделью и хранить
    ссылку в самом турнире.
    """
    competition_duration: timedelta = timedelta(hours=5)
    hint_penalty: timedelta = timedelta(minutes=15)
    wrong_attempt_penalty: timedelta = timedelta(minutes=30)
