import pickle, os

class FsaSerializer:

    def __init__(self, folder_name, logger=None):
        self.folder_name = folder_name
        self.logger = logger

    def save_fsa(self, fsa, fsa_id):
        filename = self.get_filename(fsa_id)
        # if self.logger:
        #     self.logger.write("save_fsa(): " + filename)
        with open(filename, 'wb') as f:
            pickle.dump(fsa, f, pickle.DEFAULT_PROTOCOL)

    def load_fsa(self, fsa_id):
        filename = self.get_filename(fsa_id)
        if os.path.isfile(filename):
            try:
                with open(filename, 'rb') as f:
                    return pickle.load(f)
            except:
                pass
        return None

    def get_filename(self, fsa_id):
        if self.folder_name:
            return "{}/{}.pickle".format(self.folder_name, fsa_id)
        else:
            return "{}.pickle".format(fsa_id)
