# -*- coding: utf-8 -*-

import random

import pymorphy2
import telebot
from telebot import types
from commands import Commands
from fsa import FSA

import config
#from database import DatabaseInteraction


bot = telebot.TeleBot(config.token)
morph = pymorphy2.MorphAnalyzer()
commands = Commands()

fsa = FSA()
fsa.load("bot_tree.json")

markuproot = fsa.compose_markup()
#markuproot.row(commands.id_learning, commands.id_qa)
#markuproot.row('Примеры работ', {'text': 'Наши контакты' })

with open('data/hello.txt', 'r', encoding='utf-8') as hello:
    hello = hello.readlines()

with open('data/help.txt', 'r', encoding='utf-8') as help:
    help = help.readlines()

with open('data/create.txt', 'r', encoding='utf-8') as ccreate:
    ccreate = ccreate.readlines()

@bot.message_handler(commands=['start'])
def send_message(message):
    """
    Приветственное сообщение.
    """
    bot.send_message(message.chat.id, random.choice(hello), reply_markup = markuproot)


#@bot.message_handler(func=lambda message: True, content_types=['text'])
@bot.message_handler(func = lambda message: True)
def cmd_all(message):
    command = message.text.lower()
    handle_command(message, command)


def handle_command(message, command, recursion=False):
    handled = fsa.handle_command(message, command)
    if handled:
        if fsa.current_command is None:
            bot.send_message(message.chat.id, random.choice(hello), reply_markup=markuproot)
        else:
            bot.send_message(message.chat.id, fsa.current_text, reply_markup=fsa.current_markup)
    else:
        if fsa.current_handler != '':
            fsa.command_handler(fsa.current_handler)
            handler = getattr(commands, fsa.current_handler)
            r = handler(fsa.current_command, message.text)
            if r is not None:
                if isinstance(r, str):
                    bot.send_message(message.chat.id, r, reply_markup=fsa.current_markup)
                elif not recursion:
                    bot.send_message(message.chat.id, r["text"])
                    handle_command(message, r["command"], True)

#@fsa.command_handler(command="handle_json_group")
#def handle_json_group(cmd, msg_text):
#    print(msg_text)


if __name__ == '__main__':
    print("bot has started..")
    while True:
        try:
            bot.polling(none_stop=False)
        except:
            pass

