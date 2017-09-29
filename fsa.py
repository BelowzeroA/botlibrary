from command_handlers import CommandHandlers
import telebot


class FSA:
    """
     Класс представляет собой реализацию конечного автомата для навигации по иерархической системе команд,
     а так же хранение текущего состояния пользователя.
    """

    # Поля, которые мы не сериализуем
    unstored_fields = ["command_handlers", "command_tree", "bot", "commands", "logger"]

    def __init__(self, chat_id, command_tree, bot, logger):
        self.current_command = None
        self.bot = bot
        self.command_handlers = CommandHandlers(logger)
        self.current_text = ''
        self.current_markup = ''
        self.current_handler = ''
        self.user_is_authorized = False
        self.user_phone_number = ''
        self.try_authorize = True
        self.chat_id = chat_id
        self.command_tree = command_tree
        self.logger = logger
        self.commands = self.command_tree.states_tree["commands"]
        self.properties = {}
        self.current_message = ''

    def __getstate__(self):
        """
        переопределяем __getstate__() для того чтобы возвращать кастомный словарь полей, подлежащих сериализации
        """
        return dict((key, value) for (key, value) in self.__dict__.items() if self.should_pickle(key))

    def should_pickle(self, name):
        return name not in self.unstored_fields

    def reset(self):
        self.current_command = None
        self.current_handler = ''
        self.current_text = ''

    def handle_command(self, msg, command_text):
        """
        Реализует логику обработки текущей команды пользователя
        :param msg - структура telebot.types.Message
        :param command_text - текст обрабатываемой команды
        """
        self.current_text = ''
        if command_text == 'в начало':
            self.current_command = None
            self.current_handler = ''
            return True
        if command_text == 'назад':
            self.current_handler = ''
            if self.current_command is None:
                return True
            self.current_command = self.current_command["parent"]
            if self.current_command is None:
                return True
            current_command = self.current_command
        elif command_text == '' and msg.content_type == 'contact':
            """
            Обработка команды передачи номера телефона боту
            """
            self.user_phone_number = msg.contact.phone_number
            current_command = self.current_command
            search_lambda = lambda cmd: "request_contact" in cmd and cmd["request_contact"] == True
            if current_command is None:
                current_command = self.traverse_commands(self.commands, search_lambda)
            elif "commands" in current_command:
                current_command = self.traverse_commands(current_command["commands"], search_lambda)
        else:
            current_command = self.traverse_commands(self.commands, command_text)

        if current_command is not None:
            if "parent" not in current_command:
                current_command["parent"] = self.current_command
            current_command["chat_id"] = self.chat_id
            self.navigate_command(current_command)
            if self.current_text:
                return True

        return False

    def navigate_command(self, command):
        """
        Выполняет установку нужных полей при навигации на определенную команду
        :param command:  json-структура, команда, в состояние которой нужно прийти
        :return: None
        """
        self.current_command = command
        if command is None:
            self.current_text = ''
            self.current_handler = ''
        else:
            if "text" in self.current_command:
                self.current_text = self.current_command["text"]
            if "content" in self.current_command:
                self.current_text = self.command_tree.content[self.current_command["id"]]
            if "handler" in self.current_command:
                self.current_handler = self.current_command["handler"]
        self.current_markup = self.compose_markup()

    def traverse_commands(self, commands, command_or_condition):
        """
        Ищет команду по заданным условиям
        :param commands: Массив команд, начиная с которого нужно выполнять поиск
        :param command_or_condition: если строка - значит текст команды, если лямбда - условие поиска
        :return: найденная команда
        """
        for comm in commands:
            if isinstance(command_or_condition, str):
                if comm["button_text"].lower() == command_or_condition and self.check_command_condition(comm):
                    return comm
            elif callable(command_or_condition):
                if command_or_condition(comm):
                    return comm

            if "commands" in comm:
                found = self.traverse_commands(comm["commands"], command_or_condition)
                if found is not None:
                    return found
        return None

    def authorize_user(self):
        """
        Выполняет попытку авторизации текущего пользователя через вызов CommandHandlers.authorize_user()
        :return:
        """
        if self.user_is_authorized or not self.try_authorize:
            return
        authorize_user = getattr(self.command_handlers, "authorize_user", None)
        if callable(authorize_user):
            self.command_handlers.authorize_user(self)
            self.try_authorize = False

    def handle_unrecognized_command(self, message):
        """
        Выполняет попытку обработки команды, не входящей в дерево
        :return:
        """
        unrecognized_command_handler = getattr(self.command_handlers, "unrecognized_command_handler", None)
        if callable(unrecognized_command_handler):
            return unrecognized_command_handler(self, message)

    def compose_markup(self):
        """
        Заполняет класс ReplyKeyboardMarkup для текущей команды
        :return:
        """
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
        if self.current_command is None:
            for comm in self.commands:
                if self.check_command_condition(comm):
                    markup.add(comm["button_text"])
        else:
            if "commands" in self.current_command:
                for comm in self.current_command["commands"]:
                    if self.check_command_condition(comm):
                        request_contact = "request_contact" in comm and comm["request_contact"]
                        button = telebot.types.KeyboardButton(text=comm["button_text"], request_contact=request_contact)
                        markup.add(button)
            self.add_default_nav_buttons(markup)
        return markup

    def add_default_nav_buttons(self, markup):
        """
        Добавляет навигационные кнопки Назад и В начало в класс ReplyKeyboardMarkup
        """
        markup.row("Назад", "В начало")

    def check_condition(self, condition):
        return eval(condition)

    def check_command_condition(self, command):
        condition_is_met = True
        if "condition" in command:
            condition_is_met = self.check_condition(command["condition"])
        return condition_is_met

    def redirect_on_success(self):
        if self.current_command and "redirect_on_success" in self.current_command:
            command = self.find_command_by_id(self.current_command["redirect_on_success"])
            self.navigate_command(command)

    def find_command_by_id(self, id):
        if id == "root":
            return None

    def send_message(self, message, markup=None, markdown=None):
        """
        Отправляет сообщение в чат текущему пользователю
        :param message: текст сообщения
        :param markup: класс ReplyKeyboardMarkup - кнопки к команде
        :param markdown: необходимость парсить Markdown
        :return:
        """
        if not markup:
            markup = self.compose_markup()
        if markdown:
            self.bot.send_message(self.chat_id, message, reply_markup=markup, parse_mode='Markdown')
        else:
            self.bot.send_message(self.chat_id, message, reply_markup=markup)

    def command_handler(self, handler=None, command=None):
        """
        Вызов обработчика команды через декоратор
        :param handler:
        :param command:
        :return:
        """
        def decorator(handler, msg_text):
            handler(command, msg_text)

    def write_log(self, info):
        if self.logger:
            self.logger.write(info)
