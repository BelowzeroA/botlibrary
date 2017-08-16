import telebot
from command_tree import CommandTree
from chat_manager import *
from fsa_serializer import FsaSerializer
from logger import Logger
import config


bot = telebot.TeleBot(config.token)
logger = Logger("log.txt")
command_tree = CommandTree("bot_tree.json")
fsa_serializer = FsaSerializer("fsa_data", logger)
chat_manager = ChatManager(bot, command_tree, BotMode.POLLING, fsa_serializer)
#markuproot = command_tree.get_root_markup()

# @bot.message_handler(func = lambda message: True)
@bot.message_handler(content_types=['text', 'contact'])
def cmd_all(message):
    print('message: "{}"'.format(message.text))
    command = ''
    if message.content_type != 'contact':
        command = message.text.lower()
    handle_command(message, command)


def handle_command(message, command):
    chat_manager.handle_command(message, command, False)


if __name__ == '__main__':
    print("bot has started..")
    while True:
        #try:
            bot.polling(none_stop=False)
        #except:
         #   pass

