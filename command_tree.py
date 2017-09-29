import json
import telebot


class CommandTree:

    def __init__(self, file_name):
        self.content = {}
        with open(file_name, 'r', encoding='utf-8') as f:
            self.states_tree = json.load(f)
        self.traverse_load_external_content(self.states_tree["commands"])

    def traverse_load_external_content(self, nodes):
        for node in nodes:
            if "content" in node:
                self.content[node["id"]] = self.load_external_content(node["content"])
            if "commands" in node:
                self.traverse_load_external_content(node["commands"])

    def load_external_content(self, filename):
        with open('content/' + filename, 'r', encoding='utf-8') as hello:
            return hello.read()

    def get_root_markup(self):
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard = True)
        for comm in self.states_tree["commands"]:
            markup.add(comm["button_text"])
        return markup
