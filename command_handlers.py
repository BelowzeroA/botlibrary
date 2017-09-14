import json
from urllib.request import Request, urlopen
import requests
import re
import telebot

subway_field_name = "subway"


class CommandHandlers:
    """
    Реализует обработчики команд для конкретного бота
    """

    def __init__(self, logger):
        # self.server_addr = "http://z.vardex.ru/erp.sdr/hs/bot/"
        self.server_addr = "http://iis/erp/hs/bot/"
        #self.live_support_ids = '280586415'
        self.live_support_ids = '435395826'
        self.shops_info_addr = "https://www.vardex.ru/api/v1/shops/telegram.php?KEY=fba0eede-a31f-4cc6-954d-64296e80ff45"
        self.questions = []
        self.logger = logger

    def compose_url(self, method, param):
        param_str = str(param)
        if isinstance(param, tuple):
            param_str = ''
            for i in range(len(param)):
                param_str += str(param[i]) + ('/' if i < len(param) - 1 else '')
        return self.server_addr + method + "/" + param_str  # "?sender=" + str(cmd["chat_id"])

    def request_1C(self, method, param):
        try:
            url = self.compose_url(method, param)
            """binary_data = msg_text.encode('utf-8')
            request = Request(url, data=binary_data)"""
            username = "bot"
            password = "6778"
            auth = requests.auth.HTTPBasicAuth(username, password)

            return self.get_json(url, auth)

            request = Request(url)
            raw_response = urlopen(request).read()
            return json.loads(raw_response.decode())
        except Exception as e:
            print(e)
            self.write_log(e)
            return None

    def get_json(self, url, auth):
        response = requests.get(url, auth=auth)
        return json.loads(response.text)

    def vc_get_info(self, automaton, msg_text):
        query = msg_text
        reply = {"success": False, "message": ""}
        if not msg_text and automaton.user_phone_number != '':
            if not self.try_bind(automaton, reply):
                return reply
        return reply

    def vc_forward_chat(self, automaton, msg_text):
        automaton.send_message("Перенаправил сообщение консультанту, сейчас он/она к вам постучится")
        automaton.bot.forward_message(self.live_support_ids, automaton.chat_id, automaton.current_message.message_id)
        return True

    def vc_get_balance(self, automaton, msg_text):
        query = msg_text
        reply = {"success": False, "message": ""}
        if not msg_text and automaton.user_phone_number != '':
            if not self.try_bind(automaton, reply):
                return reply

        if not all(char.isdigit() for char in msg_text) and automaton.user_is_authorized:
            query = automaton.user_phone_number

        response = self.request_1C("getbonusinfo", self.clean_query(query))
        if response:
            if response["status"] == 0:
                data = response["data"]
                reply["message"] += data["message"]
                reply["success"] = True
                return reply
            else:
                reply["message"] = response["error"]
                return reply
        return reply

    def get_shop_info(self, automaton, msg_text):
        found_shops = None
        json_response = self.get_json(self.shops_info_addr, None)
        found_cities = list((city for city in json_response["cities"] if msg_text.lower() in city["name"].lower()))
        if len(found_cities) == 0:
            found_shops = self.find_shops_near_subway(json_response["shops"], msg_text.lower())
            if len(found_shops) == 0:
                return "Нет такого города или станции метро {}".format(msg_text)

        reply = {"message": "", "markdown": True}

        if found_shops:
            reply["message"] = self.generate_shops_info(found_shops)
            return reply

        found_city_id = found_cities[0]["code"]
        shops = json_response["shops"][found_city_id]

        if len(shops) > 25:
            return self.reply_with_subway_stations(shops)
        else:
            reply["message"] = self.generate_shops_info(shops)
            return reply

    def get_service_corners(self, automaton, msg_text):
        json_response = self.get_json(self.shops_info_addr, None)
        shops = self.find_shops_withs_services(json_response["shops"])
        reply = {"message": "", "markdown": True}
        reply["message"] = self.generate_shops_info(shops, show_city=True)
        return reply

    def find_shops_withs_services(self, shops_json):
        shops = []
        for shops_info in shops_json.values():
            for shop_info in shops_info:
                if get_field_value(shop_info, "servicecenter"):
                    shops.append(shop_info)
        return shops

    def find_shops_near_subway(self, shops_json, subway):
        shops = []
        for shops_info in shops_json.values():
            for shop_info in shops_info:
                if get_field_value(shop_info, subway_field_name) == subway or \
                                get_field_value(shop_info, "city") == subway:
                    shops.append(shop_info)
        return shops

    def reply_with_subway_stations(self, shops):
        reply = {"message": "Выберите город/станцию метро"}
        subways = set()
        for shop_info in shops:
            if subway_field_name in shop_info:
                subways.add(shop_info[subway_field_name])
            else:
                subways.add(shop_info["city"])

        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
        for subway in sorted(subways):
            markup.add(subway)
        reply["markup"] = markup
        return reply

    def generate_shops_info(self, shops, show_city=False):
        reply = ''
        counter = 0
        for shop_info in shops:
            counter += 1

            city = get_field_value(shop_info, "city", lower_value=False)
            city = " г. {},".format(city) if city and show_city else ''

            subway = "м. {},".format(shop_info[subway_field_name]) \
                if subway_field_name in shop_info and shop_info[subway_field_name] else ""

            phone = shop_info["telephone"]
            phone_cleaned = self.clean_phone_number(phone)
            if phone_cleaned[0:1] == "8":
                phone_cleaned = "+7" + phone_cleaned[1:]
            else:
                phone_cleaned = "+" + phone_cleaned
            phone = "[{}](tel:{})".format(phone, phone_cleaned)
            phone_addon = shop_info["telephone_addon"]
            phone_with_addon = "{} доб. {}".format(phone, phone_addon) if phone_addon else phone

            address = (shop_info["address"] if shop_info["address"] else "")
            reply += "{}.{} {}\n  {} {} {}\n{}\n".format(counter, city, shop_info["name"], subway, address,
                                                         phone_with_addon, shop_info["schedule"])
        reply = reply.replace('&quot;', "'")
        return reply

    def get_order_state(self, automaton, msg_text):
        query = msg_text
        reply = {"success": False, "message": ""}
        if not msg_text and automaton.user_phone_number != '':
            query = automaton.user_phone_number
            if not self.try_bind(automaton, reply):
                return reply

        request_for_first_time = True
        if automaton.user_is_authorized and automaton.user_phone_number != '':
            if msg_text and any(char.isdigit() for char in msg_text):
                query = msg_text + " " + automaton.user_phone_number[1:]
                request_for_first_time = False
            else:
                query = automaton.user_phone_number

        response = self.request_1C("getorderstate", self.clean_query(query))
        if response:
            if response["status"] == 0:
                data = response["data"]
                reply["message"] += data["message"]
                if automaton.user_is_authorized and request_for_first_time:
                    reply["message"] += "\n\nВы можете узнать статус любого заказа, просто введя его номер"
                reply["success"] = True
                return reply
            else:
                reply["message"] = response["error"]
                return reply

    def get_repair_state(self, automaton, msg_text):
        query = msg_text
        reply = {"success": False, "message": ""}
        if not msg_text and automaton.user_phone_number != '':
            query = automaton.user_phone_number
            if not self.try_bind(automaton, reply):
                return reply

        if not all(char.isdigit() for char in msg_text) and automaton.user_is_authorized:
            query = automaton.user_phone_number

        response = self.request_1C("getrepairstate", self.clean_query(query))
        if response:
            if response["status"] == 0:
                data = response["data"]
                reply["message"] += data["message"]
                reply["success"] = True
                return reply
            else:
                reply["message"] = response["error"]
                return reply

    def try_bind(self, automaton, reply):
        if not automaton.user_is_authorized:
            response = self.request_1C("bindtelegramid", (automaton.chat_id, automaton.user_phone_number))
            if response:
                if response["status"] < 0:
                    reply["message"] = response["error"]
                    return False
                else:
                    reply["message"] = "Ваш Телеграм ID успешно привязан к телефону {}\n".format(
                        automaton.user_phone_number)
                    automaton.user_is_authorized = True
                    if get_field_value(response["data"], "hasBonusAccount"):
                        automaton.properties["hasBonusAccount"] = True
        return True

    def clean_query(self, query):
        parts = query.split()
        cleaned = ''
        for part in parts:
            cleaned += self.clean_phone_number(part) + ' '
        return cleaned.strip()

    def authorize_user(self, automaton):
        automaton.properties["hasBonusAccount"] = False
        response = self.request_1C("getuserphone", automaton.chat_id)
        self.write_log(response)
        if response and response["status"] == 0:
            data = response["data"]
            automaton.user_phone_number = self.clean_phone_number(data["phone_number"])
            automaton.user_is_authorized = True
            if get_field_value(response["data"], "hasBonusAccount"):
                automaton.properties["hasBonusAccount"] = True

    def unrecognized_command_handler(self, automaton, message):
        automaton.send_message("😉 вы что-то такое сказали, а я не понял. Перенаправил сообщение на техподдержку, сейчас они к вам постучатся")
        automaton.bot.forward_message(self.live_support_ids, message.chat.id, message.message_id)
        return True

    def clean_phone_number(self, phone_number):
        return re.sub('[\- +()]', '', phone_number)

    def write_log(self, info):
        if self.logger:
            self.logger.write(info)


def get_field_value(json_obj, field_name, lower_value=True):
    if field_name not in json_obj:
        return None
    else:
        value = json_obj[field_name]
        if lower_value:
            return value.lower() if isinstance(value, str) else value
        else:
            return value
