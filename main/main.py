import pandas as pd
import numpy as np
import requests
import datetime
from lib.create_db import DB

a = DB()
update = input('update database? y/n')

if update == 'y':
    a.update_db()
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
