import json
from urllib.request import Request, urlopen
import requests

class Commands:
    def __init__(self):
        self.server_addr = "http://z.vardex.ru/erp.sdr/hs/bot/"
        self.questions = []

    def compose_url(self, method, param):
        return self.server_addr + method + "/" + param#"?sender=" + str(cmd["chat_id"])

    def request_1C(self, method, param):
        try:
            url = self.compose_url(method, param)
            """binary_data = msg_text.encode('utf-8')
            request = Request(url, data=binary_data)"""
            username = "bot"
            password = "6778"
            auth = requests.auth.HTTPBasicAuth(username, password)
            response = requests.get(url, auth=auth)
            return json.loads(response.text)

            request = Request(url)
            raw_response = urlopen(request).read()
            return json.loads(raw_response.decode())
        except Exception as e:
            print(e)
            return None

    def get_shop_phones(self, cmd, msg_text):
        return "Вы выбрали город {}, а там мноого магазинов".format(msg_text)

    def get_order_state(self, cmd, msg_text):
        response = self.request_1C("getorderstate", msg_text)
        if response:
            if response["status"] == 0:
                data = response["data"]
                return "Заказ {} в статусе '{}', примерная дата доставки {}"\
                    .format(msg_text, data["status"], data["deliveryDate"])
            else:
                return "Заказ {} не найден в нашей базе".format(msg_text)

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
        self.questions.clear()
        if response["ok"] == True:
            return { "text": "Данные успешно загружены", "command": "назад" }
        else:
            return "Ошибка: " + response["error"] + "\n " + response["description"]