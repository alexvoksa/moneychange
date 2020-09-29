import requests
import pandas as pd
import datetime
from lib.create_db import DB
import telebot

db_cls = DB()

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

CURRENCIES_LIST = db_cls.names_curr['name'].to_list()
CURRENCIES_LIST = '\n'.join([str(i) for i in CURRENCIES_LIST])
with open('../data/token.txt', 'r') as f:
    TOKEN = f.read()

bot = telebot.TeleBot(TOKEN)


@bot.message_handler(commands=['start'])
def welcome(message):
    bot.send_message(message.chat.id, WELCOME_MESSAGE)


@bot.message_handler(commands=['curr'])
def curr_list(message):
    print('User ' + message.chat.id + ' asked for curr list')
    bot.send_message(message.chat.id, CURRENCIES_LIST)


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

        log_string = str(message.chat.id) + ',' + str(from_) + ',' + str(to_) + ',' + str(amount_) + ',' + str(response_len)
        DB.write_log(timestamp, log_string, 'user')

        if response_len > 0:
            string_result = '\n\n'.join([str(i) for i in search_result.values])
        else:
            string_result = 'Ничего не найдено, хуевые валюты ты подбираешь, пидар'
        bot.send_message(message.chat.id, string_result)
    else:
        bot.send_message(message.chat.id, HELP_MESSAGE)


@bot.message_handler(content_types=['text'])
def help_msg(message):
    bot.send_message(message.chat.id, HELP_MESSAGE)


bot.polling()
