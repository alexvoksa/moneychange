import requests
import pandas as pd
import numpy as np
import datetime
from lib.create_db import DB
import telebot
from telebot import types
import time

db_cls = DB()
df_curr = pd.read_csv('../data/all_curr_full.csv')


def search_curr(type_):
    return np.array(df_curr[df_curr['type_short'] == type_][['code', 'desc']])


fiat = search_curr('fiat')
crypto = search_curr('crypto')
ecomm = search_curr('ecomm')
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
CURRENCIES_LIST = db_cls.names_curr
CURRENCIES_DICT = CURRENCIES_LIST.to_dict()
CURRENCIES_LIST = '\n'.join(['|'.join(i[:3]) for i in CURRENCIES_LIST.values])

with open('../data/token.txt', 'r') as f:
    TOKEN = f.read()

bot = telebot.TeleBot(TOKEN)


@bot.message_handler(commands=['start'])
def welcome(message):
    bot.send_message(message.chat.id, WELCOME_MESSAGE)


@bot.message_handler(commands=['curr'])
def curr_list(message):
    print('User ' + str(message.chat.id) + ' asked for curr list')
    pass
    # bot.send_message(message.chat.id, CURRENCIES_LIST)


@bot.message_handler(commands=['change'])
def change_curr(message):
    timestamp = str(datetime.datetime.now().strftime("%d:%m:%Y_%H:%M:%S"))
    text_input = message.text.split('_')
    if len(text_input) > 1:
        print(message.chat.id, text_input)
        from_ = text_input[0].replace('/change ', '').upper()
        to_ = text_input[1].upper()
        amount_ = float(text_input[2].replace(',', '.'))

        search_result = db_cls.search(from_, to_, amount_)
        response_len = len(search_result)

        log_string = str(message.chat.id) + ',' + str(from_) + ',' + str(to_) + ',' + str(amount_) + ',' + str(
            response_len)
        DB.write_log(timestamp, log_string, 'user')

        if response_len > 0:
            string_result = '\n\n'.join([CURRENCIES_MESSAGE.format(str(i[1]), str(amount_), str(i[2]),
                                                                   str(i[5]), str(i[3]),
                                                                   str(i[0])).replace('_', ' ')
                                         for i in search_result.values])
            # response[['timestamp', 'www', 'from', 'to', 'course', 'new_amount']]
        else:
            string_result = 'Ничего не найдено, хуевые валюты ты подбираешь, пидар'
        bot.send_message(message.chat.id, string_result, parse_mode='html')
    else:
        bot.send_message(message.chat.id, HELP_MESSAGE)


# from = 1, to = 2, fiat = f, crypto = c, ecomm = e, None = 0


@bot.message_handler(commands=['cd'])
def start_change(message):
    qstring = '{}_{}_{}_{}_{}_{}_{}_{}'
    keyboard = types.InlineKeyboardMarkup(row_width=3)
    fiat_str = ['1', 'f'] + ['0'] * 6
    crypto_str = ['1', 'c'] + ['0'] * 6
    ecomm_str = ['1', 'e'] + ['0'] * 6
    fiat_button = types.InlineKeyboardButton(text="FIAT", callback_data=qstring.format(*fiat_str))
    crypto_button = types.InlineKeyboardButton(text="CRYPTO", callback_data=qstring.format(*crypto_str))
    ecomm_button = types.InlineKeyboardButton(text="ECOMM", callback_data=qstring.format(*ecomm_str))
    keyboard.row(*[fiat_button, crypto_button, ecomm_button])
    bot.send_message(message.chat.id, 'What you want to change from?', reply_markup=keyboard)


@bot.callback_query_handler(lambda query: all(
    [query.data.split('_')[0] == '1'] +
    [query.data.split('_')[1] != '0'] +
    ['0' == i for i in query.data.split('_')[2:]]
)
                            )
def step_one(query):
    idx = query.data.split('_')[1]
    qstring = '1_{}'.format(idx) + '_{}_{}_{}_{}_{}_{}'

    if idx == 'f':
        row_width = 2
        keyboard = types.InlineKeyboardMarkup(row_width=row_width)
        fiat_buttons = [types.InlineKeyboardButton(text=i[1],
                                                   callback_data=qstring.format(*([i[0]] +
                                                                                  ['0'] * 5))) for i in fiat]
        shift = 2
        for start in range(0, len(fiat_buttons) - shift + 1, 2):
            keyboard.row(*list(fiat_buttons[start:start + shift]))
        bot.send_message(query.message.chat.id, 'Change FROM?', reply_markup=keyboard)

    elif idx == 'c':
        row_width = 3
        crypto_keyboard = types.InlineKeyboardMarkup(row_width=row_width)
        crypto_buttons = [types.InlineKeyboardButton(text=i[0],
                                                     callback_data=qstring.format(*([i[0]] +
                                                                                    ['0'] * 5))) for i in crypto]
        for start in range(0, len(crypto_buttons) - row_width + 1, row_width):
            crypto_keyboard.row(*list(crypto_buttons[start:start + row_width]))
        bot.send_message(query.message.chat.id, 'Change FROM?', reply_markup=crypto_keyboard)

    elif idx == 'e':
        row_width = 2
        ecomm_keyboard = types.InlineKeyboardMarkup(row_width=row_width)
        ecomm_buttons = [types.InlineKeyboardButton(text=i[1],
                                                    callback_data=qstring.format(*([i[0]] +
                                                                                   ['0'] * 5))) for i in ecomm]
        for start in range(0, len(ecomm_buttons) - row_width + 1, row_width):
            ecomm_keyboard.row(*list(ecomm_buttons[start:start + row_width]))
        bot.send_message(query.message.chat.id, 'Change FROM?', reply_markup=ecomm_keyboard)
    else:
        print('error 0001, wrong splitter or wrong id')


@bot.callback_query_handler(lambda query: all(
    [query.data.split('_')[0] == '1'] +
    [query.data.split('_')[1] != '0'] +
    [query.data.split('_')[2] != '0'] +
    ['0' == i for i in query.data.split('_')[3:]]
)
                            )
def step_two(query):

    idx_one = query.data.split('_')[1]
    idx_two = query.data.split('_')[2]
    qstring = '1_{}_{}'.format(*[idx_one, idx_two]) + '_{}_{}_{}_{}_{}'

    keyboard = types.InlineKeyboardMarkup(row_width=3)
    fiat_str = ['2', 'f'] + ['0'] * 3
    crypto_str = ['2', 'c'] + ['0'] * 3
    ecomm_str = ['2', 'e'] + ['0'] * 3

    fiat_button = types.InlineKeyboardButton(text="FIAT", callback_data=qstring.format(*fiat_str))
    crypto_button = types.InlineKeyboardButton(text="CRYPTO", callback_data=qstring.format(*crypto_str))
    ecomm_button = types.InlineKeyboardButton(text="ECOMM", callback_data=qstring.format(*ecomm_str))
    keyboard.row(*[fiat_button, crypto_button, ecomm_button])

    bot.send_message(query.message.chat.id, 'Change ' + idx_two + ' TO ?', reply_markup=keyboard)
    print(qstring)


@bot.callback_query_handler(lambda query: all(
    [query.data.split('_')[0] == '1'] +
    [query.data.split('_')[1] != '0'] +
    [query.data.split('_')[2] != '0'] +
    [query.data.split('_')[3] == '2'] +
    [query.data.split('_')[4] != '0'] +
    ['0' == i for i in query.data.split('_')[5:]]
)
                            )
def step_one(query):

    # idx_zero = 1
    idx_one = query.data.split('_')[1]
    idx_two = query.data.split('_')[2]
    # idx_three =  2
    idx_four = query.data.split('_')[4]

    qstring = '1_{}_{}_2_{}_'.format(*[idx_one, idx_two, idx_four]) + '{}_{}_{}'
    print(qstring)
    if idx_four == 'f':
        row_width = 2
        keyboard = types.InlineKeyboardMarkup(row_width=row_width)
        fiat_buttons = [types.InlineKeyboardButton(text=i[1],
                                                   callback_data=qstring.format(*([i[0]] + ['a'] +
                                                                                  ['0']))) for i in fiat]
        shift = 2
        for start in range(0, len(fiat_buttons) - shift + 1, 2):
            keyboard.row(*list(fiat_buttons[start:start + shift]))
        bot.send_message(query.message.chat.id, 'Change FROM?', reply_markup=keyboard)

    elif idx_four == 'c':
        row_width = 3
        crypto_keyboard = types.InlineKeyboardMarkup(row_width=row_width)
        crypto_buttons = [types.InlineKeyboardButton(text=i[0],
                                                     callback_data=qstring.format(*([i[0]] + ['a'] +
                                                                                    ['0']))) for i in crypto]
        for start in range(0, len(crypto_buttons) - row_width + 1, row_width):
            crypto_keyboard.row(*list(crypto_buttons[start:start + row_width]))
        bot.send_message(query.message.chat.id, 'Change FROM?', reply_markup=crypto_keyboard)

    elif idx_four == 'e':
        row_width = 2
        ecomm_keyboard = types.InlineKeyboardMarkup(row_width=row_width)
        ecomm_buttons = [types.InlineKeyboardButton(text=i[1],
                                                    callback_data=qstring.format(*([i[0]] + ['a'] +
                                                                                   ['0']))) for i in ecomm]
        for start in range(0, len(ecomm_buttons) - row_width + 1, row_width):
            ecomm_keyboard.row(*list(ecomm_buttons[start:start + row_width]))
        bot.send_message(query.message.chat.id, 'Change FROM?', reply_markup=ecomm_keyboard)
    else:
        print('error 0001, wrong splitter or wrong id')
    print(qstring)


@bot.callback_query_handler(lambda query: all(
    [query.data.split('_')[0] == '1'] +
    [query.data.split('_')[1] != '0'] +
    [query.data.split('_')[2] != '0'] +
    [query.data.split('_')[3] == '2'] +
    [query.data.split('_')[4] != '0'] +
    [query.data.split('_')[5] != '0'] +
    [query.data.split('_')[6] == 'a'] +
    [query.data.split('_')[7] == '0']
                                            )
                            )
def amount_get(query):
    bot.send_message(query.message.chat.id, 'Enter money amount you want to change')


bot.polling(none_stop=True)
