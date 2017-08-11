import telebot
from command_tree import CommandTree
from chat_manager import ChatManager
from logger import Logger
import config


bot = telebot.TeleBot(config.token)
logger = Logger("/srv/www/vardex.ru/public_html/telegram/log.txt")
command_tree = CommandTree("bot_tree.json")
chat_manager = ChatManager(bot, command_tree)
markuproot = command_tree.get_root_markup()


@bot.message_handler(commands=['start'])
def send_message(message):
    """
    Приветственное сообщение.
    """
    bot.send_message(message.chat.id, chat_manager.hello_message, reply_markup = markuproot)


@bot.message_handler(func = lambda message: True)
def cmd_all(message):
    print('message: "{}"'.format(message.text))
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

