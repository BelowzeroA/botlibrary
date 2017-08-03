import json

class CommandTree:

    def load(self, data_file):
        self.states_tree = json.load(data_file)