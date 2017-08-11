import json
from telebot import types

class CommandTree:

    def __init__(self, file_name):
        with open(file_name, 'r', encoding='utf-8') as f:
            self.states_tree = json.load(f)

    def get_root_markup(self):
        markup = types.ReplyKeyboardMarkup(resize_keyboard = True)
        for comm in self.states_tree["commands"]:
            markup.add(comm["button_text"])
        return markup
