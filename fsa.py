from commands import Commands
import json
from telebot import types


class FSA:

    def __init__(self):
        self.current_command = None
        self.commands = Commands()
        self.states_tree = ''
        self.current_text = ''
        self.current_markup = ''
        self.current_handler = ''
        self.chat_id = ''

    def load(self, filename):
        with open(filename, 'r', encoding='utf-8') as data_file:
            self.states_tree = json.load(data_file)

    def handle_command(self, msg, command_text):
        self.current_text = ''
        self.chat_id = msg.chat.id
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
        else:
            current_command = self.traverse_commands(self.states_tree["commands"], command_text)

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


    def traverse_commands(self, commands, command_text):

        for comm in commands:
            if comm["button_text"].lower() == command_text:
                return comm
            if "commands" in comm:
                found = self.traverse_commands(comm["commands"], command_text)
                if found is not None:
                    return found
        return None

    def compose_markup(self):
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        if self.current_command is None:
            for comm in self.states_tree["commands"]:
                markup.add(comm["button_text"])
        else:
            if "commands" in self.current_command:
                for comm in self.current_command["commands"]:
                    markup.add(comm["button_text"])
            markup.row("Назад", "В начало")
        return markup

    def command_handler(self, handler=None, command=None):
        def decorator(handler, msg_text):
            handler(command, msg_text)