from fsa import FSA
from command_handlers import CommandHandlers

class ChatManager:

    def __init__(self, bot, command_tree):
        self.chats = {}
        self.bot = bot
        self.command_tree = command_tree
        self.command_handlers = CommandHandlers()

        with open('data/hello.txt', 'r', encoding='utf-8') as hello:
            self.hello_message = hello.read()

    def handle_command(self, message, command, recursion=False):

        chat_id = message.chat.id
        if chat_id in self.chats:
            automaton = self.chats[chat_id]
        else:
            automaton = FSA(chat_id, self.command_tree, self.bot)
            self.chats[chat_id] = automaton

        handled = automaton.handle_command(message, command)
        if handled:
            if automaton.current_command is None:
                automaton.send_message(self.hello_message, self.command_tree.get_root_markup())
            elif automaton.current_text:
                automaton.send_message(automaton.current_text, automaton.current_markup)
        else:
            if automaton.current_handler != '':
                automaton.command_handler(automaton.current_handler)
                handler = getattr(self.command_handlers, automaton.current_handler)
                r = handler(automaton.current_command, message.text)
                if r is not None:
                    if isinstance(r, str):
                        automaton.send_message(r, automaton.current_markup)
                    elif not recursion:
                        automaton.send_message(automaton.chat_id, r["text"])
                        self.handle_command(message, r["command"], True)