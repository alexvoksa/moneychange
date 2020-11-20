import requests
import pandas as pd
import numpy as np
import datetime
import time
import json
from lib.Verification import UserCheck

CHANGE_STR = 'Обмен {} на {}.\n' \
             'Введите сумму, которую Вы хотите обменять'

CURRENCIES_MESSAGE = '{}\n' \
                     '<pre>' \
                     '|  IN    |{} {}|\n' \
                     '|  OUT   |<b>{} {}</b>|\n' \
                     '|VALID ON|{} MSK|' \
                     '</pre>'

WELCOME_MESSAGE = 'Допустимые команды:\n' \
                  '/start - открыть начальный экран\n' \
                  '/cc - найти обменник с лучшим курсом\n' \
                  '/ck - проверить кошелек отправителя\n' \
                  '/ph - проверить номер телефона отправителя\n' \
                  '/ip - проверить IP отправителя\n' \
                  '/eml - проверить email отправителя'

PHONE_MESSAGE_INFO = '<pre>Данные по номеру: {}\n' \
                     'Характеристика: {}\n' \
                     'Категория владельца: {}\n' \
                     'Тип номера телефона: {}\n' \
                     'Страна: {}\n' \
                     'Отзывы:\n' \
                     '{}\n' \
                     '{}\n' \
                     '{}\n</pre>'

PHONE_MESSAGE_NO_INFO = '<pre>Номер {} отсутствует в базе</pre>'

IP_MESSAGE_INFO = '<pre>Данные по IP: {}\n' \
                  'Город: {}\n' \
                  'Страна: {}\n' \
                  'Использование proxy: {}\n' \
                  'Использование VPN: {}\n' \
                  'Использование Tor: {}</pre>'

IP_MESSAGE_NO_INFO = '<pre>IP-адрес {} отсутствует в базе</pre>'

HELP_MESSAGE = 'NONE_STR'

CHANGE_FAULT = 'По вашему запросу ничего не найдено.\n' \
               'Попробуйте изменить валюту или сумму к обмену.'


class BotCommander:
    def __init__(self, TOKEN, COUNTER, COURSES, VERIFICATION):
        self.token = TOKEN
        self.counter = COUNTER
        self.engine = COURSES
        self.verifier = VERIFICATION
        self.urlstring = 'https://api.telegram.org/bot{}/'.format(self.token) + '{}'
        self.response = requests.post(url=self.urlstring.format('getUpdates'))
        self.updates = json.loads(self.response.content)
        try:
            self.query = self.updates['result']
        except KeyError:
            requests.post(self.urlstring.format('deleteWebhook'))
            try:
                self.query = self.updates['result']
            except Exception:
                print('No new messages. Wait for new messages before using functions')
                self.query = []
        self.currency_frame = pd.read_csv('../data/all_curr_full.csv')

        self.fiat = BotCommander.generate_curr_arrays('fiat', self.currency_frame)
        self.crypto = BotCommander.generate_curr_arrays('crypto', self.currency_frame)
        self.ecomm = BotCommander.generate_curr_arrays('ecomm', self.currency_frame)

        self.fiat_list = [i[0] for i in self.fiat]
        self.crypto_list = [i[0] for i in self.crypto]
        self.ecomm_list = [i[0] for i in self.ecomm]

        self.start_buttons = [{"text": str(i[0]), "callback_data": str(i[1])} for i in [('Найти обменник', '/cc'),
                                                                                        ('Проверить кошелек', '/ck'),
                                                                                        ('Проверить телефон', '/ph'),
                                                                                        ('Проверить IP', '/ip'),
                                                                                        ('Проверить Email', '/eml')]]

        self.fiat_buttons_from = [{"text": str(i[1]), "callback_data": 'from_' + str(i[0])} for i in self.fiat]
        self.crypto_buttons_from = [{"text": str(i[0]), "callback_data": 'from_' + str(i[0])} for i in self.crypto]
        self.ecomm_buttons_from = [{"text": str(i[1]), "callback_data": 'from_' + str(i[0])} for i in self.ecomm]

        self.fiat_buttons_to = [{"text": str(i[1]), "callback_data": 'amount_' + str(i[0])} for i in self.fiat]
        self.crypto_buttons_to = [{"text": str(i[0]), "callback_data": 'amount_' + str(i[0])} for i in self.crypto]
        self.ecomm_buttons_to = [{"text": str(i[1]), "callback_data": 'amount_' + str(i[0])} for i in self.ecomm]

        '''final buttons, that used in bot'''
        # these two stands for currency type: FIAT, CRYPTO and ECOMM
        # and this one stands for 'from' callback query
        self.buttons_type_from = {"chat_id": "", "text": "Отдаю",
                                  "reply_markup": {"inline_keyboard": [
                                      [{"text": "FIAT", "callback_data": "fiat_from"},
                                       {"text": "CRYPTO", "callback_data": "crypto_from"},
                                       {"text": "ECOMM", "callback_data": "ecomm_from"}]
                                  ]
                                  }
                                  }
        # and this one stands for 'to' callback query
        self.buttons_type_to = {"chat_id": "", "text": "Получаю",
                                "reply_markup": {"inline_keyboard": [
                                    [{"text": "FIAT", "callback_data": "fiat_to"},
                                     {"text": "CRYPTO", "callback_data": "crypto_to"},
                                     {"text": "ECOMM", "callback_data": "ecomm_to"}]
                                ]
                                }
                                }
        # These three stands for 'from' callback query, that calls back when one of
        # 'FIAT', 'CRYPTO' or 'ECOMM' buttons were pressed first time
        self.buttons_fiat_from = {"chat_id": "", "text": "Обмен с фиатных валюты", "reply_markup":
            {"inline_keyboard": BotCommander.create_buttons_row(2, self.fiat_buttons_from)
             }
                                  }
        self.buttons_crypto_from = {"chat_id": "", "text": "Обмен с криптовалют", "reply_markup":
            {"inline_keyboard": BotCommander.create_buttons_row(3, self.crypto_buttons_from)
             }
                                    }
        self.buttons_ecomm_from = {"chat_id": "", "text": "Обмен с E-commerce", "reply_markup":
            {"inline_keyboard": BotCommander.create_buttons_row(2, self.ecomm_buttons_from)
             }
                                   }
        # These three stands for 'to' callback query, that calls back when one of
        # 'FIAT', 'CRYPTO' or 'ECOMM' buttons were pressed second time
        self.buttons_fiat_to = {"chat_id": "", "text": "Обмен на фиатные валюты", "reply_markup":
            {"inline_keyboard": BotCommander.create_buttons_row(2, self.fiat_buttons_to)
             }
                                }
        self.buttons_start = {"chat_id": "", "text": "Что Вы хотите сделать", "reply_markup":
            {"inline_keyboard": BotCommander.create_buttons_row(1, self.start_buttons)
             }
                              }
        self.buttons_crypto_to = {"chat_id": "", "text": "Обмен на криптовалюлты", "reply_markup":
            {"inline_keyboard": BotCommander.create_buttons_row(3, self.crypto_buttons_to)
             }
                                  }
        self.buttons_ecomm_to = {"chat_id": "", "text": "Обмен на E-commerce", "reply_markup":
            {"inline_keyboard": BotCommander.create_buttons_row(2, self.ecomm_buttons_to)
             }
                                 }

        self.data = {}
        # {'chat_id': {'status': None, 'check':None, 'user_id': None, 'first_name': None, 'username': None,
        #                'language_code': None, 'date': None, 'from': None, 'to': None, 'amount': None}}

    @staticmethod
    def create_buttons_row(shift, buttons_list):
        """
        This func generates buttons row. Takes list with dict of
        button name and callback_query response that will be sent to server
        when user presses on button
        :param shift: integer
        :param buttons_list: list of dicts
        :return: list
        """
        return [buttons_list[start:start + shift] for start in range(0, len(buttons_list) - shift + 1, shift)]

    @staticmethod
    def generate_curr_arrays(type_, dataframe):
        return np.array(dataframe[dataframe['type_short'] == type_][['code', 'desc']])

    def __update_user_info(self, type_,  response):
        if type_ == 'callback':
            chat_id = response['callback_query']['message']['chat']['id']
            user_id = response['callback_query']['from']['id']
            first_name = response['callback_query']['from']['first_name']
            username = response['callback_query']['from']['username']
            language_code = response['callback_query']['from']['language_code']
        elif type_ == 'message':
            chat_id = response['message']['chat']['id']
            user_id = response['message']['from']['id']
            first_name = response['message']['from']['first_name']
            username = response['message']['from']['username']
            language_code = response['message']['from']['language_code']
        try:
            if self.data[chat_id]:
                pass
        except KeyError:
            self.data.update({chat_id: {}})
        self.data[chat_id]['user_id'] = user_id
        self.data[chat_id]['first_name'] = first_name
        self.data[chat_id]['username'] = username
        self.data[chat_id]['language_code'] = language_code

    def update(self):
        """
        This function uses short-polling and looking for new data
        After receiving json file from Telegram server it decodes file
        and appends it to existing query parameter in class BotCommander
        :return:
        """
        self.response = requests.post(url='https://api.telegram.org/bot{}/getUpdates'.format(self.token))
        self.updates = json.loads(self.response.content)
        self.query = self.query + self.updates['result']

    def send_message(self, chat_id, text, parse_mode='HTML'):
        """
        This func create POST-request and sends it to a Telegram server
        As a result, user with necessary chat_id will receive message with
        'text'. You can use MarkdownV2
        :param parse_mode: MarkdownV2, HTML(by default), Markdown
        :param chat_id: integer
        :param text: string
        :return: POST-request to a Telegram server
        """
        if parse_mode == 'HTML':
            send_string = 'sendMessage?chat_id={}&text={}&parse_mode=HTML'\
                .format(chat_id, text)
            requests.post(url=self.urlstring.format(send_string))
        else:
            send_string = 'sendMessage?chat_id={}&text={}&parse_mode={}'\
                .format(chat_id, text, parse_mode)
            requests.post(url=self.urlstring.format(send_string))

    def get_last_message(self):
        """
        This func update query with a POST-request and get text of a last
        user message, that was sent to the bot
        May be useful for logging and watching for client troubles.
        At this time have no use in this script
        :return: print to the Python console user parameters and text of the last
        user message
        """
        self.update()
        response_ = [self.updates['result'][-1]['message']['from']['id'],
                     self.updates['result'][-1]['message']['from']['first_name'],
                     self.updates['result'][-1]['message']['from']['username'],
                     self.updates['result'][-1]['message']['from']['language_code'],
                     self.updates['result'][-1]['message']['chat']['id'],
                     self.updates['result'][-1]['message']['date'],
                     self.updates['result'][-1]['message']['text']
                     ]
        response_ = [str(i) for i in response_]
        print('id {} name {} username {}, language {},\nChat id {}, datestamp {}, text:\n\n{}'.format(*response_))

    def send_button(self, button_dict, chat_id):
        button_dict['chat_id'] = chat_id
        urls = self.urlstring.format('sendMessage')
        requests.post(urls, json=json.loads(json.dumps(button_dict)))

    def proceed_query(self, response):
        print(response)
        if 'callback_query' in response:
            chat_id = response['callback_query']['message']['chat']['id']
            self.__update_user_info('callback', response)
            data = response['callback_query']['data']
            # <-- incoming callback query [fiat_from, crypto_from, ecomm_from]
            if 'fiat_from' in data:
                self.send_button(button_dict=self.buttons_fiat_from, chat_id=chat_id)
            elif 'crypto_from' in data:
                self.send_button(button_dict=self.buttons_crypto_from, chat_id=chat_id)
            elif 'ecomm_from' in data:
                self.send_button(button_dict=self.buttons_ecomm_from, chat_id=chat_id)
            # --> outgoing query [from_CurrName]
            # <-- incoming query [from_CurrName]
            elif 'from_' in data:
                base_dict_from = self.data[response['callback_query']['message']['chat']['id']]
                base_dict_from['timestamp_from'] = response['callback_query']['message']['date']
                base_dict_from['from'] = data
                self.data[response['callback_query']['message']['chat']['id']] = base_dict_from
                print(self.data)
                self.send_button(button_dict=self.buttons_type_to, chat_id=chat_id)
            # --> outgoing query [fiat_to, crypto_to, ecomm_to]
            # <-- incoming query [fiat_to, crypto_to, ecomm_to]
            elif 'fiat_to' in data:
                self.send_button(button_dict=self.buttons_fiat_to, chat_id=chat_id)
            elif 'crypto_to' in data:
                self.send_button(button_dict=self.buttons_crypto_to, chat_id=chat_id)
            elif 'ecomm_to' in data:
                self.send_button(button_dict=self.buttons_ecomm_to, chat_id=chat_id)
            # --> outgoing query [amount_CurrName]

            # <-- incoming query [amount_CurrName]
            elif 'amount_' in data:
                print(self.data)
                base_dict_to = self.data[response['callback_query']['message']['chat']['id']]
                base_dict_to['timestamp_to'] = response['callback_query']['message']['date']
                base_dict_to['to'] = data
                base_dict_to['status'] = 1
                print(base_dict_to)
                from_what = base_dict_to['from'].split('_')[1]
                to_what = base_dict_to['to'].split('_')[1]
                self.data[response['callback_query']['message']['chat']['id']] = base_dict_to
                print(self.data)
                self.send_message(chat_id=chat_id, text=CHANGE_STR.format(from_what, to_what))

            elif '/cc' in data:
                chat_id = response['callback_query']['message']['chat']['id']
                self.send_button(button_dict=self.buttons_type_from, chat_id=chat_id)

            elif '/ck' in data:
                chat_id = response['callback_query']['message']['chat']['id']
                self.data[response['callback_query']['message']['chat']['id']]['check'] = 1
                self.send_message(chat_id=chat_id, text='Введите номер кошелька отправителя \n'
                                                        'для проверки')

            elif '/ph' in data:
                chat_id = response['callback_query']['message']['chat']['id']
                self.data[response['callback_query']['message']['chat']['id']]['phone'] = 1
                self.send_message(chat_id=chat_id, text='Введите номер телефона для проверки')

            elif '/ip' in data:
                chat_id = response['callback_query']['message']['chat']['id']
                self.data[response['callback_query']['message']['chat']['id']]['ip'] = 1
                self.send_message(chat_id=chat_id, text='Введите IP для проверки')

            elif '/eml' in data:
                chat_id = response['callback_query']['message']['chat']['id']
                self.data[response['callback_query']['message']['chat']['id']]['eml'] = 1
                self.send_message(chat_id=chat_id, text='Введите адрес эл.почты для проверки')

            # NO QUERY
            else:
                chat_id = response['callback_query']['message']['chat']['id']
                self.send_message(chat_id=chat_id, text='NO QUERY ERROR')

        elif ('message' in response) and ('/start' in response['message']['text']):
            chat_id = response['message']['chat']['id']
            self.send_button(button_dict=self.buttons_start, chat_id=chat_id)

        elif ('message' in response) and ('/cc' in response['message']['text']):
            chat_id = response['message']['chat']['id']
            self.send_button(button_dict=self.buttons_type_from, chat_id=chat_id)

        elif ('message' in response) and ('/ck' in response['message']['text']):
            self.__update_user_info('message', response)
            chat_id = response['message']['chat']['id']
            self.data[response['message']['chat']['id']]['check'] = 1
            self.send_message(chat_id=chat_id, text='Введите номер кошелька отправителя \n'
                                                    'для проверки')

        elif ('message' in response) and ('/ph' in response['message']['text']):
            self.__update_user_info('message', response)
            chat_id = response['message']['chat']['id']
            self.data[response['message']['chat']['id']]['phone'] = 1
            self.send_message(chat_id=chat_id, text='Введите номер телефона для проверки')

        elif ('message' in response) and ('/ip' in response['message']['text']):
            self.__update_user_info('message', response)
            chat_id = response['message']['chat']['id']
            self.data[response['message']['chat']['id']]['ip'] = 1
            self.send_message(chat_id=chat_id, text='Введите IP для проверки')

        elif ('message' in response) and ('/eml' in response['message']['text']):
            self.__update_user_info('message', response)
            chat_id = response['message']['chat']['id']
            self.data[response['message']['chat']['id']]['eml'] = 1
            self.send_message(chat_id=chat_id, text='Введите адрес эл.почты для проверки')

        elif 'message' in response:
            self.__update_user_info('message', response)
            counter = 0
            try:
                if self.data[response['message']['chat']['id']]['status'] == 1:
                    amount_base_dict = self.data[response['message']['chat']['id']]
                    amount_base_dict['timestamp_amount'] = response['message']['date']
                    amount_base_dict['amount'] = response['message']['text']
                    amount_base_dict['status'] = 0
                    self.data[response['message']['chat']['id']] = amount_base_dict
                    from_ = self.data[response['message']['chat']['id']]['from'].split('_')[1]
                    to_ = self.data[response['message']['chat']['id']]['to'].split('_')[1]
                    amount_ = float(self.data[response['message']['chat']['id']]['amount'])
                    response_query = self.engine.search(from_, to_, amount_, use_archived=True)
                    response_len = len(response_query)
                    if response_len > 0:
                        string_result = '\n\n'.join([str(i) for i in response_query.values])
                        string_result = '\n\n'.join([CURRENCIES_MESSAGE.format(str(i[1]), str(amount_), str(i[2]),
                                                                               str(i[5]), str(i[3]),
                                                                               str(i[0])).replace('_', ' ')
                                                     for i in response_query.values])
                        self.send_message(chat_id=response['message']['chat']['id'], text=string_result)
                    else:
                        self.send_message(chat_id=response['message']['chat']['id'], text=CHANGE_FAULT)
                    counter += 1
            except KeyError:
                pass
            try:
                if self.data[response['message']['chat']['id']]['check'] == 1:
                    self.data[response['message']['chat']['id']]['check'] = 0
                    wallet_id = str(response['message']['text'])
                    wallet_answer = self.verifier.check_user(wallet_id)
                    self.send_message(chat_id=response['message']['chat']['id'], text=wallet_answer)
                else:
                    pass
                counter += 1
            except KeyError:
                pass
            try:
                if self.data[response['message']['chat']['id']]['phone'] == 1:
                    self.data[response['message']['chat']['id']]['phone'] = 0
                    phone_number = str(response['message']['text'])
                    phone_answer = UserCheck.check_phone(phone_number, 5)
                    if len(phone_answer) == 6:
                        answer_str = PHONE_MESSAGE_INFO.format(phone_answer['number'],
                                                               phone_answer['rating_category'],
                                                               phone_answer['caller_type'],
                                                               phone_answer['number_type'],
                                                               phone_answer['country'],
                                                               phone_answer['first'],
                                                               '',
                                                               '')
                    elif len(phone_answer) == 7:
                        answer_str = PHONE_MESSAGE_INFO.format(phone_answer['number'],
                                                               phone_answer['rating_category'],
                                                               phone_answer['caller_type'],
                                                               phone_answer['number_type'],
                                                               phone_answer['country'],
                                                               phone_answer['first'],
                                                               phone_answer['second'],
                                                               '')
                    elif len(phone_answer) == 8:
                        answer_str = PHONE_MESSAGE_INFO.format(phone_answer['number'],
                                                               phone_answer['rating_category'],
                                                               phone_answer['caller_type'],
                                                               phone_answer['number_type'],
                                                               phone_answer['country'],
                                                               phone_answer['first'],
                                                               phone_answer['second'],
                                                               phone_answer['third'])
                    else:
                        answer_str = PHONE_MESSAGE_NO_INFO.format(phone_answer['number'])
                    self.send_message(chat_id=response['message']['chat']['id'], text=answer_str)
                    counter += 1
            except KeyError:
                pass
            try:
                if self.data[response['message']['chat']['id']]['ip'] == 1:
                    self.data[response['message']['chat']['id']]['ip'] = 0
                    ip = pd.Series([str(response['message']['text'])])
                    ip_answer = UserCheck.get_info_from_ip(ip)
                    print(ip_answer)
                    if isinstance(ip_answer[3][0], float):
                        ip_str = IP_MESSAGE_NO_INFO.format(ip[0])
                    else:
                        ip_str = IP_MESSAGE_INFO.format(ip[0],
                                                        ip_answer[0][0],
                                                        ip_answer[1][0],
                                                        ip_answer[3][0].is_public_proxy,
                                                        ip_answer[3][0].is_anonymous_vpn,
                                                        ip_answer[3][0].is_tor_exit_node
                                                        )
                    self.send_message(chat_id=response['message']['chat']['id'], text=ip_str)
                    counter += 1
                else:
                    pass
            except KeyError:
                pass
            try:
                if self.data[response['message']['chat']['id']]['eml'] == 1:
                    self.data[response['message']['chat']['id']]['eml'] = 0
                    self.send_message(chat_id=response['message']['chat']['id'], text='PASS')
                    counter += 1
                else:
                    pass
            except KeyError:
                pass
            if counter == 0:
                self.send_message(chat_id=response['message']['chat']['id'], text=WELCOME_MESSAGE)
            else:
                pass
        else:
            print('Err')

    def start(self, update_counter):
        print('Bot ONLINE')
        with open('../data/LAST_UPDATE.txt', 'a') as container:
            while True:
                for i in self.query:
                    update_counter = int(update_counter)
                    if i['update_id'] > update_counter:
                        self.proceed_query(i)
                        update_counter = str(i['update_id'])
                        container.write('\n')
                        container.write(update_counter)
                    else:
                        pass
                self.update()

