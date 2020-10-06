import pandas as pd
import numpy as np
import requests
import datetime
from lib.create_db import DB
from lib.telegram_bot import BotCommander
import time

commander = BotCommander()


if __name__ == '__main__':

    a = DB()
    while True:
        a.update_db()
        time.sleep(15)









"""
a = DB()
update = input('update database? y/n')
archive = input('archive database? y/n')

if update == 'y':
    if archive == 'y':
        a.update_db(archive=True)
    else:
        a.update_db(archive=False)
else:
    pass

while True:
    money_from = str(input('Change from?'))
    money_to = str(input('Change to?'))
    money_amount = float(input('Amount?'))
    a.search(money_from, money_to, money_amount)
    end_ = input('Continue y/n ?')
    if end_ == 'y':
        continue
    else:
        break
"""