from logger import Logger
logger = Logger("/srv/www/vardex.ru/public_html/telegram/log.txt")

import telebot
from telebot import types
from command_tree import CommandTree
from chat_manager import *
from fsa_serializer import FsaSerializer
import config

try:
    bot = telebot.TeleBot(config.token)
    command_tree = CommandTree("bot_tree.json")
    fsa_serializer = FsaSerializer("fsa_data", logger)
    # fsa_serializer = FsaSerializer('', logger)
    chat_manager = ChatManager(bot, command_tree, BotMode.WEBHOOK, fsa_serializer, logger)
    #logger.write(chat_manager)
except Exception as e:
    logger.write(e)


def application(env, start_response):
    """
    Входная точка бота в режиме WEBHOOK
    :param env:
    :param start_response:
    :return:
    """
    error_str = ''
    try:
        request_body_size = int(env['CONTENT_LENGTH'])
        request_body = env['wsgi.input'].read(request_body_size)
        request_json = request_body.decode("utf-8")
        update = types.Update.de_json(request_json)
        cmd_all(update.message)
        #logger.write(update)
        #bot.process_new_updates([update])

    except Exception as e:
        error_str = 'Something went wrong:' + str(e)
        logger.write(e)

    start_response('200 OK', [('Content-Type','text/html')])

    if error_str:
        b = bytearray()
        b.extend(error_str.encode())
        return [b]
    else:
        return [""]


def cmd_all(message):
    command = ''
    logger.write("message: {}".format(message))
    if message.content_type != 'contact':
        command = message.text.lower()
    handle_command(message, command)

def handle_command(message, command):
    chat_manager.handle_command(message, command, False)
