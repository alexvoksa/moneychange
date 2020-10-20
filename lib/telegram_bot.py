import requests
import pandas as pd
import numpy as np
import datetime
import time
import json
from lib.create_db import DB

with open('../data/token.txt', 'r') as f:
    TOKEN = f.read()

CURRENCIES_MESSAGE = '{}\n' \
                     '<pre>' \
                     '|  IN    |{} {}|\n' \
                     '|  OUT   |<b>{} {}</b>|\n' \
                     '|VALID ON|{} MSK|' \
                     '</pre>'

WELCOME_MESSAGE = 'Привет, кожаный ублюдок! \n\n' \
                  'Я - твой финансовый бог, слушай меня и я помогу тебе ' \
                  'безпрепятственно и с минимальными потерями \n\n' \
                  ' обменять валюту в этих ваших интернетах.\n\n\n ' \
                  'Для оптимального результата выбери из выпадающего списка валюту,\n\n' \
                  ' которую ты отдаешь и валюту, которую тебе необходимо получть. \n' \
                  ' Не забудь указать сумму обмена, от этого зависит количество обменников,\n' \
                  ' которые будут отображены для лучшего результата.'

HELP_MESSAGE = 'Если ты, Лебовский, решил узнать где деньги, команды следующие.\n' \
               'Чтобы увидеть наше охуительное приветствие - вводи /start \n' \
               'Чтобы увидеть список всех доступных валют - введи /curr \n' \
               'Если ты - ублюдок, мать твою, решил ко мне лезть - вводи \n' \
               ' /change С_НА_СУММА'


class BotCommander:
    def __init__(self, TOKEN):
        self.urlstring = 'https://api.telegram.org/bot{}/'.format(TOKEN) + '{}'
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

        self.fiat_buttons_from = [{"text": str(i[1]), "callback_data": 'from_' + str(i[0])} for i in self.fiat]
        self.crypto_buttons_from = [{"text": str(i[0]), "callback_data": 'from_' + str(i[0])} for i in self.crypto]
        self.ecomm_buttons_from = [{"text": str(i[1]), "callback_data": 'from_' + str(i[0])} for i in self.ecomm]

        self.fiat_buttons_to = [{"text": str(i[1]), "callback_data": 'amount_' + str(i[0])} for i in self.fiat]
        self.crypto_buttons_to = [{"text": str(i[0]), "callback_data": 'amount_' + str(i[0])} for i in self.crypto]
        self.ecomm_buttons_to = [{"text": str(i[1]), "callback_data": 'amount_' + str(i[0])} for i in self.ecomm]

        '''final buttons, that used in bot'''
        # these two stands for currency type: FIAT, CRYPTO and ECOMM
        # and this one stands for 'from' callback query
        self.buttons_type_from = {"chat_id": "", "text": "Change FROM?",
                                  "reply_markup": {"inline_keyboard": [
                                      [{"text": "FIAT", "callback_data": "fiat_from"},
                                       {"text": "CRYPTO", "callback_data": "crypto_from"},
                                       {"text": "ECOMM", "callback_data": "ecomm_from"}]
                                  ]
                                  }
                                  }
        # and this one stands for 'to' callback query
        self.buttons_type_to = {"chat_id": "", "text": "Change TO?",
                                "reply_markup": {"inline_keyboard": [
                                    [{"text": "FIAT", "callback_data": "fiat_to"},
                                     {"text": "CRYPTO", "callback_data": "crypto_to"},
                                     {"text": "ECOMM", "callback_data": "ecomm_to"}]
                                ]
                                }
                                }
        # These three stands for 'from' callback query, that calls back when one of
        # 'FIAT', 'CRYPTO' or 'ECOMM' buttons were pressed first time
        self.buttons_fiat_from = {"chat_id": "", "text": "Change FIAT?", "reply_markup":
            {"inline_keyboard": BotCommander.create_buttons_row(2, self.fiat_buttons_from)
             }
                                  }
        self.buttons_crypto_from = {"chat_id": "", "text": "Change CRYPTO?", "reply_markup":
            {"inline_keyboard": BotCommander.create_buttons_row(3, self.crypto_buttons_from)
             }
                                    }
        self.buttons_ecomm_from = {"chat_id": "", "text": "Change ECOMM?", "reply_markup":
            {"inline_keyboard": BotCommander.create_buttons_row(2, self.ecomm_buttons_from)
             }
                                   }
        # These three stands for 'to' callback query, that calls back when one of
        # 'FIAT', 'CRYPTO' or 'ECOMM' buttons were pressed second time
        self.buttons_fiat_to = {"chat_id": "", "text": "Change FIAT?", "reply_markup":
            {"inline_keyboard": BotCommander.create_buttons_row(2, self.fiat_buttons_to)
             }
                                }
        self.buttons_crypto_to = {"chat_id": "", "text": "Change CRYPTO?", "reply_markup":
            {"inline_keyboard": BotCommander.create_buttons_row(3, self.crypto_buttons_to)
             }
                                  }
        self.buttons_ecomm_to = {"chat_id": "", "text": "Change ECOMM?", "reply_markup":
            {"inline_keyboard": BotCommander.create_buttons_row(2, self.ecomm_buttons_to)
             }
                                 }

        self.data = {}
        # {'chat_id': {'status': None, 'user_id': None, 'first_name': None, 'username': None,
        #                'language_code': None, 'date': None, 'from': None, 'to': None, 'amount': None}}
        self.engine = DB()

    @staticmethod
    def create_buttons_row(shift, buttons_list):
        return [buttons_list[start:start + shift] for start in range(0, len(buttons_list) - shift + 1, shift)]

    @staticmethod
    def generate_curr_arrays(type_, dataframe):
        return np.array(dataframe[dataframe['type_short'] == type_][['code', 'desc']])

    def update(self):
        self.response = requests.post(url='https://api.telegram.org/bot{}/getUpdates'.format(TOKEN))
        self.updates = json.loads(self.response.content)
        self.query = self.query + self.updates['result']

    def send_message(self, chat_id, text):
        send_string = 'sendMessage?chat_id={}&text={}'.format(chat_id, text)
        requests.post(url=self.urlstring.format(send_string))

    def get_last_message(self):
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
        if 'callback_query' in response:
            chat_id = response['callback_query']['message']['chat']['id']
            user_id = response['callback_query']['from']['id']
            first_name = response['callback_query']['from']['first_name']
            username = response['callback_query']['from']['username']
            language_code = response['callback_query']['from']['language_code']
            try:
                type(self.data[chat_id])
            except KeyError:
                self.data.update({chat_id: {}})
            self.data[chat_id]['user_id'] = user_id
            self.data[chat_id]['first_name'] = first_name
            self.data[chat_id]['username'] = username
            self.data[chat_id]['language_code'] = language_code

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
                self.data[response['callback_query']['message']['chat']['id']] = base_dict_to
                print(self.data)
                self.send_message(chat_id=chat_id, text='Enter money amount you want to change')
            # NO QUERY
            else:
                self.send_message(chat_id=chat_id, text='Ты пидар')

        elif ('message' in response) and ('/start' in response['message']['text']):
            chat_id = response['message']['chat']['id']
            self.send_button(button_dict=self.buttons_type_from, chat_id=chat_id)

        elif ('message' in response) and (self.data[response['message']['chat']['id']]['status'] == 1):
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
            print('Err')


a = BotCommander(TOKEN)
