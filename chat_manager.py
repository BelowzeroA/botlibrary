from enum import Enum
from fsa import FSA
from command_handlers import CommandHandlers

class BotMode(Enum):
    WEBHOOK = 1
    POLLING = 2

class ChatManager:

    def __init__(self, bot, command_tree, mode=BotMode.POLLING, serializer=None):
        self.chats = {}
        self.bot = bot
        self.mode = mode
        self.command_tree = command_tree
        self.command_handlers = CommandHandlers()
        self.fsa_serializer = serializer

        with open('data/hello.txt', 'r', encoding='utf-8') as hello:
            self.hello_message = hello.read()

    def handle_command(self, message, command, recursion=False):

        chat_id = message.chat.id
        automaton = self.get_automaton(chat_id)
        automaton.authorize_user()

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
                r = handler(automaton, message.text)
                if r is not None:
                    if isinstance(r, str):
                        automaton.send_message(r, automaton.current_markup)
                    elif not recursion:
                        automaton.send_message(automaton.chat_id, r["text"])
                        self.handle_command(message, r["command"], True)

        if self.mode == BotMode.WEBHOOK:
            self.fsa_serializer.save_fsa(automaton, chat_id)


    def get_automaton(self, chat_id):
        if self.mode == BotMode.POLLING:
            if chat_id in self.chats:
                automaton = self.chats[chat_id]
            else:
                automaton = FSA(chat_id, self.command_tree, self.bot)
                self.chats[chat_id] = automaton
        else:
            assert self.fsa_serializer != None, "Property 'fsa_serializer' must be set in 'webhook' mode"
            automaton = FSA(chat_id, self.command_tree, self.bot)
            automaton_loaded = self.fsa_serializer.load_fsa(chat_id)
            if automaton_loaded:
                filtered_fields = {key : value for key, value in automaton_loaded.__dict__.items() if key not in FSA.unstored_fields}
                automaton.__dict__.update(filtered_fields)

        return automaton

