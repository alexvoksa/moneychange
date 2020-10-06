import requests
import pandas as pd
import numpy as np
import datetime
import time
import json

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
        self.query = self.updates['result']
        self.currency_frame = pd.read_csv('../data/all_curr_full.csv')
        self.fiat = BotCommander.generate_curr_arrays('fiat', self.currency_frame)
        self.crypto = BotCommander.generate_curr_arrays('crypto', self.currency_frame)
        self.ecomm = BotCommander.generate_curr_arrays('ecomm', self.currency_frame)
        self.fiat_list = [i[0] for i in self.fiat]
        self.crypto_list = [i[0] for i in self.crypto]
        self.ecomm_list = [i[0] for i in self.ecomm]
        self.fiat_btns = [{"text":str(i[1]), "callback_data": str(i[0])} for i in self.fiat]
        self.crypto_btns = [{"text": str(i[0]), "callback_data": str(i[0])} for i in self.crypto]
        self.ecomm_btns = [{"text": str(i[1]), "callback_data": str(i[0])} for i in self.ecomm]

        self.buttons_type = {
                            "chat_id": "{}",
                            "text": "Change type?",
                            "reply_markup": {
                                "inline_keyboard":   [[
                                                      {
                                                        "text": "FIAT",
                                                        "callback_data": "fiat_from"
                                                      },
                                                      {
                                                        "text": "CRYPTO",
                                                        "callback_data": "crypto_from"
                                                      },
                                                      {
                                                        "text": "ECOMM",
                                                        "callback_data": "ecomm_from"
                                                      }
                                                      ]]
                                            }
                                        }
        self.buttons_fiat = {"chat_id": "", "text": "Change FIAT?", "reply_markup":
            {"inline_keyboard": BotCommander.create_buttons_row(2, self.fiat_btns)
            }
        }
        self.buttons_crypto = {"chat_id": "", "text": "Change CRYPTO?", "reply_markup":
            {"inline_keyboard": BotCommander.create_buttons_row(3, self.crypto_btns)
            }
                             }
        self.buttons_ecomm = {"chat_id": "", "text": "Change ECOMM?", "reply_markup":
            {"inline_keyboard": BotCommander.create_buttons_row(2, self.ecomm_btns)
            }
                             }

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
        print(self.urlstring.format(send_string))

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
            data = response['callback_query']['data']
            if 'fiat_from' in data:
                self.send_button(button_dict=self.buttons_fiat, chat_id=chat_id)
            elif 'crypto_from' in data:
                self.send_button(button_dict=self.buttons_crypto, chat_id=chat_id)
            elif 'ecomm_from' in data:
                self.send_button(button_dict=self.buttons_ecomm, chat_id=chat_id)
            else:
                self.send_message(chat_id=chat_id, text='Menya ne vzali v mail.ru')



"""
    @staticmethod
    def make_list(make_from, addition):
        return [addition + i[0] for i in make_from]

    def welcome(self, message_chat_id):
        self.bot.send_message(message_chat_id, BotCommander.WELCOME_MESSAGE)

    @staticmethod
    def curr_list(message_chat_id):
        print('User ' + str(message_chat_id) + ' asked for curr list')

    def change_curr(self, message_chat_id, message_text_input):
        timestamp = str(datetime.datetime.now().strftime("%d:%m:%Y_%H:%M:%S"))
        text_input = message_text_input.split('_')
        if len(text_input) > 1:
            print(message_chat_id, text_input)
            from_ = text_input[0].replace('/change ', '').upper()
            to_ = text_input[1].upper()
            amount_ = float(text_input[2].replace(',', '.'))
            search_result = BotCommander.db_cls.search(from_, to_, amount_)
            response_len = len(search_result)

            log_string = str(message_chat_id) + \
                         ',' + \
                         str(from_) + \
                         ',' + \
                         str(to_) + \
                         ',' + \
                         str(amount_) + \
                         ',' + \
                         str(response_len)

            DB.write_log(timestamp, log_string, 'user')

            if response_len > 0:
                string_result = '\n\n'.join([
                    BotCommander.CURRENCIES_MESSAGE.format(str(i[1]),
                                                           str(amount_),
                                                           str(i[2]),
                                                           str(i[5]),
                                                           str(i[3]),
                                                           str(i[0])).replace('_', ' ') for i in search_result.values
                ])
                # response[['timestamp', 'www', 'from', 'to', 'course', 'new_amount']]
            else:
                string_result = 'Ничего не найдено, хуевые валюты ты подбираешь, пидар'
            self.bot.send_message(message_chat_id, string_result, parse_mode='html')
        else:
            self.bot.send_message(message_chat_id, BotCommander.HELP_MESSAGE)

    def choose_type_of_curr(self, query, dict_, epoch):
        keyboard = types.InlineKeyboardMarkup(row_width=3)
        fiat_str = 'fiat' + '_' + epoch
        crypto_str = 'crypto' + '_' + epoch
        ecomm_str = 'ecomm' + '_' + epoch
        fiat_button = types.InlineKeyboardButton(text="FIAT", callback_data=fiat_str)
        crypto_button = types.InlineKeyboardButton(text="CRYPTO", callback_data=crypto_str)
        ecomm_button = types.InlineKeyboardButton(text="ECOMM", callback_data=ecomm_str)
        keyboard.row(*[fiat_button, crypto_button, ecomm_button])
        self.bot.send_message(query.message.chat.id, 'Change {}'.format(epoch), reply_markup=keyboard)
        print(dict_)

    @staticmethod
    def fill_buttons(source, add, row_width, no_crypt=True):
        keyboard = types.InlineKeyboardMarkup(row_width=row_width)
        if no_crypt:
            buttons = [types.InlineKeyboardButton(text=i[1], callback_data=add + '_' + i[0]) for i in source]
        else:
            buttons = [types.InlineKeyboardButton(text=i[0], callback_data=add + '_' + i[0]) for i in source]
        for start in range(0, len(source) - row_width + 1, row_width):
            keyboard.row(*list(buttons[start:start + row_width]))
        return keyboard

    # choose_name_of_curr(query, q_dict, 'from', add='from')
    def choose_name_of_curr(self, query, dict_, epoch, add):
        if dict_[epoch] == 'fiat_from':
            keyboard = BotCommander.fill_buttons(source=fiat, add=add, row_width=2)
            self.bot.send_message(query.message.chat.id, 'Which {}?'.format(epoch), reply_markup=keyboard)
        elif dict_[epoch] == 'crypto_from':
            keyboard = BotCommander.fill_buttons(source=crypto, add=add, row_width=3, no_crypt=False)
            self.bot.send_message(query.message.chat.id, 'Which {}?'.format(epoch), reply_markup=keyboard)
        elif dict_[epoch] == 'ecomm_from':
            keyboard = BotCommander.fill_buttons(source=ecomm, add=add, row_width=2)
            self.bot.send_message(query.message.chat.id, 'Which {}?'.format(epoch), reply_markup=keyboard)
        else:
            print('error 0001, wrong splitter or wrong id')
        print(dict_)

    def start_change(self, message):
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        start_button = types.InlineKeyboardButton(text="Start!", callback_data='start')
        keyboard.row(start_button)
        self.bot.send_message(message.chat.id, 'You want to start?', reply_markup=keyboard)

    def start_change(self, message):
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        start_button = types.InlineKeyboardButton(text="Start!", callback_data='start')
        keyboard.row(start_button)
        self.bot.send_message(message.chat.id, 'You want to start?', reply_markup=keyboard)

    def step_one(self, query):
        """ At this step nothing will be writen in the dictionary!!!!!!!!!!! """
        self.choose_type_of_curr(query, self.q_dict, 'from')

    def change_from(self, query):
        self.choose_name_of_curr(query, self.q_dict, 'from', add='from')

    def change_to(self, query):
        self.q_dict['to'] = query.data
        self.choose_name_of_curr(query, self.q_dict, 'to', add='to')

    def change_fiat(self, query):
        self.q_dict['from'] = query.data
        self.choose_type_of_curr(query, q_dict, 'from')

"""