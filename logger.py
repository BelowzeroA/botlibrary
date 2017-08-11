import sys, traceback

class Logger:

    def __init__(self, filename):
        self.filename = filename

    def write(self, info):
        print(info)
        presentation = str(info)
        if isinstance(info, Exception):
            exc_type, exc_value, exc_tb = sys.exc_info()
            filename, line_num, func_name, text = traceback.extract_tb(exc_tb)[-1]
            full_tb_text = traceback.extract_tb(exc_tb)
            presentation = "Exception: {} \nin {} at line {} \n traceback: {}".format(presentation, filename, line_num, full_tb_text)

        text_file = open(self.filename, "w")
        text_file.write(presentation)
        text_file.close()
