import json
import requests
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class Commands:
    def __init__(self):
        self.server_addr = "http://api.itsgreat.ru/"
        self.questions = []

    def compose_url(self, method, cmd):
        return self.server_addr + method + "?token=testtoken&sender=" + str(cmd["chat_id"])

    def store_reply_group(self, cmd, msg_text):
        url = self.compose_url("learn/store_reply_group", cmd)
        binary_data = msg_text.encode('utf-8')
        request = Request(url, data=binary_data)
        raw_response = urlopen(request).read()
        return json.loads(raw_response.decode())

    def handle_json_group(self, cmd, msg_text):
        response = self.store_reply_group(cmd, msg_text)
        if response["ok"] == True:
            return "Данные успешно загружены. Вы можете загрузить другую порцию данных в том же формате"
        else:
            return "Ошибка: " + response["error"] + "\n " + response["description"]

    def handle_string_question(self, cmd, msg_text):
        words = msg_text.split()
        if len(words) < 3:
            return "Вопрос должен содержать не менее 3 слов"
        self.questions.append(msg_text)
        return "Добавлено {} вопрос(ов)".format(len(self.questions))

    def handle_string_answer(self, cmd, msg_text):
        if len(self.questions) == 0:
            return "Вы не добавили ни одного вопроса"
        json_str_a = '"a": "{}", '.format(msg_text)
        json_str_qs = ''
        for q in self.questions:
            json_str_qs += '"{}", '.format(q)
        json_str_qs = json_str_qs[:-2]
        json_str_qs = '"qs": [ {} ]'.format(json_str_qs)
        json_str = '{' + json_str_a + json_str_qs + '}'
        response = self.store_reply_group(cmd, json_str)
        if response["ok"] == True:
            return { "text": "Данные успешно загружены", "command": "назад" }
        else:
            return "Ошибка: " + response["error"] + "\n " + response["description"]