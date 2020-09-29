import requests
import pandas as pd
import datetime
from tqdm import tqdm
from time import sleep

import telebot

WELCOME_MESSAGE = 'Hello bitches'
FROM_MESSAGE = ''
TO_MESSAGE = ''
AMOUNT_MESSAGE = ''

with open('../data/token.txt', 'r') as f:
    TOKEN = f.read()

bot = telebot.TeleBot(TOKEN)


@bot.message_handler(commands=['start'])
def welcome(message):
    bot.send_message(message.chat.id, WELCOME_MESSAGE)


@bot.message_handler(content_types=['text'])
def income(message):
    INCOME_CURR =  message.text

    bot.send_message(message.chat.id, FROM_MESSAGE)
    elif
