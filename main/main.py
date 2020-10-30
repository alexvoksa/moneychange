from lib.create_db import DB
from lib.telegram_bot import BotCommander
from lib.preprocessing import Preprocessor, OUTPUT_NONE_STRING, OUTPUT_STRING
import time

databaser = DB()
commander = BotCommander()
verificator = Preprocessor()
counter = -1

if __name__ == '__main__':
    commander.start(-1)










