from command_handlers import CommandHandlers
#from telebot import types
import telebot


class FSA:

    unstored_fields = ["command_handlers", "command_tree", "bot", "commands"]

    def __init__(self, chat_id, command_tree, bot):
        self.current_command = None
        self.bot = bot
        self.command_handlers = CommandHandlers()
        self.current_text = ''
        self.current_markup = ''
        self.current_handler = ''
        self.user_is_authorized = False
        self.user_phone_number = ''
        self.chat_id = chat_id
        self.command_tree = command_tree
        self.commands = self.command_tree.states_tree["commands"]

    def __getstate__(self):
        return dict((key, value) for (key, value) in self.__dict__.items() if self.should_pickle(key))

    def should_pickle(self, name):
        return name not in self.unstored_fields

    def handle_command(self, msg, command_text):
        self.current_text = ''
        if command_text == 'в начало':
            self.current_command = None
            return True
        if command_text == 'назад':
            if self.current_command is None:
                return True
            self.current_command = self.current_command["parent"]
            if self.current_command is None:
                return True
            current_command = self.current_command
        elif command_text == '' and msg.content_type == 'contact':
            self.user_phone_number = msg.contact.phone_number
            current_command = self.current_command
            if current_command is None:
                current_command = self.traverse_commands(self.commands,
                    lambda cmd: "request_contact" in cmd and cmd["request_contact"] == True)
        else:
            current_command = self.traverse_commands(self.commands, command_text)

        if current_command is not None:

            if "parent" not in current_command:
                current_command["parent"] = self.current_command

            current_command["chat_id"] = self.chat_id

            self.current_command = current_command

            if "text" in self.current_command:
                self.current_text = self.current_command["text"]

            self.current_markup = self.compose_markup()

            if "handler" in self.current_command:
                self.current_handler = self.current_command["handler"]

            if self.current_text:
                return True

        return False

    def traverse_commands(self, commands, command_or_condition):

        for comm in commands:
            if isinstance(command_or_condition, str):
                if comm["button_text"].lower() == command_or_condition:
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
        if self.user_is_authorized:
            return
        authorize_user = getattr(self.command_handlers, "authorize_user", None)
        if callable(authorize_user):
            self.command_handlers.authorize_user(self)

    def compose_markup(self):
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
            markup.row("Назад", "В начало")
        return markup

    def check_condition(self, condition):
        return eval(condition)

    def check_command_condition(self, command):
        condition_is_met = True
        if "condition" in command:
            condition_is_met = self.check_condition(command["condition"])
        return condition_is_met

    def send_message(self, message, markup):
        self.bot.send_message(self.chat_id, message, reply_markup=markup)

    def command_handler(self, handler=None, command=None):
        def decorator(handler, msg_text):
            handler(command, msg_text)
