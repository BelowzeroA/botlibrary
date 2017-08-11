import json
#from telebot import types
import telebot
import _types

class CommandTree:

    def __init__(self, file_name):
        with open(file_name, 'r', encoding='utf-8') as f:
            self.states_tree = json.load(f)

    def get_root_markup(self):
        #markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard = True)
        markup = _types.ReplyKeyboardMarkup(resize_keyboard=True)
        for comm in self.states_tree["commands"]:
            markup.add(comm["button_text"])
        return markup
