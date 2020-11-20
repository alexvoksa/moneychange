from lib.create_db import DB
from lib.telegram_bot import BotCommander
from lib.preprocessing import Preprocessor
from lib.Verification import UserCheck
import time

with open('../data/LAST_UPDATE.txt', 'r') as counter:
    COUNTER = counter.readlines()[-1]

with open('../data/token.txt', 'r') as f:
    TOKEN = f.read()

COURSES = DB()
# COURSES.update_db()
VERIFICATION = Preprocessor()
BOT = BotCommander(TOKEN, COUNTER, COURSES, VERIFICATION)

if __name__ == '__main__':
    BOT.start(COUNTER)










