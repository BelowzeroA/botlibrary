class Commands:
    def __init__(self):
        self.id_mainmenu = "Главное меню"
        self.id_learning = "Обучение"
        self.id_qa = "Вопрос-ответ"
        self.id_as_json = "В виде json"
        self.id_back = "Назад"
        self.id_step_by_step = "Пошаговый ввод"
        self.prompts = \
            { self.id_as_json : 'Введите группу ответ-вопросы в формате json. Пример:\n '
                                '{ "a": "answer text", "qs" : ["question 1", "question 2", "question 3" ] }',
              self.id_learning: 'Выберите способ обучения'
            }

    def is_text_command(self, text, cmd):
        lowered = text.lower()
        for id, name in self.cmds.items():
            if name.lower() == lowered and id == cmd:
                return True
        return False
