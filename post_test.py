from urllib.request import Request, urlopen


server_addr = "http://api.itsgreat.ru/"
url = server_addr + "learn/store_reply_group?token=testtoken"
msg_text = """{ "a": "reply text",
"qs" : [
"а курьеру можно оплатить заказ картой на месте?",
"скажите а курьер принимает безналом?",
"вопрос. а можно купить товар за безналичный расчет?"
] }"""
binary_data = msg_text.encode('utf-8')
request = Request(url, data=binary_data)
json = urlopen(request).read()
print(json)