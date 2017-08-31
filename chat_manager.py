from enum import Enum
from fsa import FSA
from command_handlers import CommandHandlers

class BotMode(Enum):
    WEBHOOK = 1
    POLLING = 2

class ChatManager:
    """
    Класс для управления чатами в режиме POLLING или обработки текущей команды в режиме WEBHOOK
    """
    def __init__(self, bot, command_tree, mode=BotMode.POLLING, serializer=None, logger=None):
        self.chats = {}
        self.bot = bot
        self.mode = mode
        self.command_tree = command_tree
        self.command_handlers = CommandHandlers(logger)
        self.fsa_serializer = serializer
        self.logger = logger

        with open('data/hello.txt', 'r', encoding='utf-8') as hello:
            self.hello_message = hello.read()

    def handle_command(self, message, command, recursion=False):
        """
        Обработчик текущей команды. Находит нужный автомат и передает ему команду на обработку
        """
        chat_id = message.chat.id
        automaton = self.get_automaton(chat_id)
        automaton.current_message = message
        automaton.authorize_user()

        handled = automaton.handle_command(message, command)
        if handled:
            if automaton.current_command is None:
                self.send_start_message(automaton)
            elif automaton.current_text:
                automaton.send_message(automaton.current_text, automaton.current_markup)
        else:
            if automaton.current_handler != '':
                self.handle_custom_command(automaton, message)
            elif command == "/start":
                automaton.reset()
                self.send_start_message(automaton)
            else:
                # unrecognized command
                result = automaton.handle_unrecognized_command(message)
                if result is None:
                    self.send_start_message(automaton)

        if self.mode == BotMode.WEBHOOK:
            self.fsa_serializer.save_fsa(automaton, chat_id)

    def handle_custom_command(self, automaton, message):
        automaton.command_handler(automaton.current_handler)
        handler = getattr(self.command_handlers, automaton.current_handler)
        r = handler(automaton, message.text)
        if r is not None:
            if isinstance(r, str):
                automaton.send_message(r, automaton.current_markup)
            elif isinstance(r, dict):
                markup = None
                markdown = None
                if "success" in r and r["success"]:
                    automaton.redirect_on_success()
                if "markup" in r:
                    markup = r["markup"]
                    automaton.add_default_nav_buttons(markup)
                if "markdown" in r:
                    markdown = True
                automaton.send_message(r["message"], markup, markdown)
            # elif not recursion:
            #     automaton.send_message(automaton.chat_id, r["text"])
            #     self.handle_command(message, r["command"], True)

    def send_start_message(self, automaton):
        automaton.send_message(self.hello_message, automaton.compose_markup(), markdown=True)

    def get_automaton(self, chat_id):
        """
        Получает конечный автомат для конкретного пользователя
        Находим в словаре (в режиме POLLING) или загружаем из pickle (в режиме WEBHOOK) автомат по ID пользователя
        Если сохраненного автомата нет, создаем его и помещаем в хранилище
        """
        if self.mode == BotMode.POLLING:
            if chat_id in self.chats:
                automaton = self.chats[chat_id]
            else:
                automaton = FSA(chat_id, self.command_tree, self.bot, self.logger)
                self.chats[chat_id] = automaton
        else:
            assert self.fsa_serializer != None, "Property 'fsa_serializer' must be set in 'webhook' mode"
            automaton = FSA(chat_id, self.command_tree, self.bot, self.logger)
            automaton_loaded = self.fsa_serializer.load_fsa(chat_id)
            if automaton_loaded:
                filtered_fields = {key : value for key, value in automaton_loaded.__dict__.items() if key not in FSA.unstored_fields}
                automaton.__dict__.update(filtered_fields)

        return automaton

    def write_log(self, info):
        if self.logger:
            self.logger.write(info)
