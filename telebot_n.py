# -*- coding: utf-8 -*-

import random

import pymorphy2
import telebot
from telebot import types
from commands import Commands

import config
#from database import DatabaseInteraction


bot = telebot.TeleBot(config.token)
morph = pymorphy2.MorphAnalyzer()
commands = Commands()

markuproot = types.ReplyKeyboardMarkup(resize_keyboard=True)
#markup.row('/create', '/verify', '/verify3')
markuproot.row(commands.id_learning, commands.id_qa)
markuproot.row('Примеры работ', {'text': 'Наши контакты' })

markup_learning = types.ReplyKeyboardMarkup(resize_keyboard=True)
#markup.row('/create', '/verify', '/verify3')
markup_learning.row(commands.id_as_json, commands.id_step_by_step)
markup_learning.row(commands.id_mainmenu)

markup_backwards = types.ReplyKeyboardMarkup(resize_keyboard=True)
markup_backwards.row(commands.id_back, commands.id_mainmenu)

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
    if command == commands.id_learning.lower():
        bot.send_message(message.chat.id, commands.prompts[commands.id_learning], reply_markup = markup_learning)
    if command == commands.id_mainmenu.lower():
        bot.send_message(message.chat.id, "главное меню", reply_markup = markuproot)
    if command == commands.id_as_json.lower():
        bot.send_message(message.chat.id, commands.prompts[commands.id_as_json], reply_markup = markup_backwards)

@bot.message_handler(commands=['помощь'])
def send_message(message):
    """
    Приветственное сообщение.
    """
    bot.send_message(message.chat.id, random.choice(help), reply_markup=markup_learning)


if __name__ == '__main__':
    print("bot has started..")
    bot.polling(none_stop=False)

