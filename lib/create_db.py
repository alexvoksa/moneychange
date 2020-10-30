import requests
import pandas as pd
import datetime
from lxml import objectify
from tqdm import tqdm
import time

COLUMNS = ['timestamp', 'www', 'from', 'to', 'in', 'out', 'amount', 'fromfee', 'tofee', 'minfee', 'city',
           'minamount', 'maxamount', 'param']
PATH_USR_LOGS = '../data/user_logs.txt'
PATH_SEARCH_LOGS = '../data/search_logs.txt'
PATH_DB_LOGS = '../data/logs.txt'
PATH_INPUT_HINT = 'Paste correct path to log file'
DATEFORMAT = "%d:%m:%Y_%H:%M:%S"
PATH_CURRENCIES = '../data/currencies.csv'
PATH_ARCHIVE_CURRENCIES = '../data/archive_currencies.csv'
PATH_LINKS = '../data/links.csv'
PATH_NAMES_CURR = '../data/all_curr_full.csv'


class DB:

    def __init__(self):
        self.links = pd.read_csv(PATH_LINKS, header=None)
        self.db = pd.DataFrame(columns=COLUMNS)
        self.names_curr = pd.read_csv(PATH_NAMES_CURR)
        self.response = None

    @staticmethod
    def request(url_link):
        try:
            response = requests.get(url_link).text.encode()
        except requests.exceptions.RequestException:
            counter = 0
            while counter < 10:
                try:
                    time.sleep(10)
                    response = requests.get(url_link).text.encode()
                    break
                except requests.exceptions.RequestException:
                    counter += 1
        # checking if 'response' variable exists
        try:
            if response:
                return response
        except NameError:
            return 1

    @staticmethod
    def write_log(time_, text, log):
        if log == 'user':
            path = PATH_USR_LOGS
        elif log == 'search':
            path = PATH_SEARCH_LOGS
        elif log == 'db':
            path = PATH_DB_LOGS
        else:
            path = input(PATH_INPUT_HINT)
        with open(path, 'a') as f:
            f.write(str(time_) + ',' + text + '\n')

    @staticmethod
    def xml2df(link_):
        super_xml = pd.DataFrame(columns=COLUMNS)
        # getting web-adress of site
        www = link_.split('/')[2]
        timestamp = str(datetime.datetime.now().strftime(DATEFORMAT))

        text_response = DB.request(link_)
        if text_response != 1:
            xml = objectify.fromstring(text_response)
            main_tree = xml.getroottree().getroot()
            for i in main_tree.getchildren():
                search_field = i.getchildren()
                tags = [i.tag for i in search_field]
                text_values = [i.text for i in search_field]
                tags.extend(['www', 'timestamp'])
                text_values.extend([www, timestamp])
                super_xml = pd.concat([super_xml, pd.DataFrame([text_values], columns=tags)], ignore_index=True)
                super_xml = super_xml.astype(str)
        return super_xml

    @staticmethod
    def update_db(archive=False):
        # This method can update current database and archive (append it) to a CSV-file
        links = pd.read_csv(PATH_LINKS, header=None)
        print('Updating database...')
        db = pd.DataFrame(columns=COLUMNS)
        for i in tqdm(links[0].tolist()):
            df = DB.xml2df(i)
            db = pd.concat([db, df], ignore_index=True)
        # some currencies comes with currency name, for example 100 USD
        # these two list comprehensives removes currency name from DataFrame
        db['minamount'] = [i.split(' ')[0] if type(i) == str else i for i in db['minamount']]
        db['maxamount'] = [i.split(' ')[0] if type(i) == str is not None else i for i in db['maxamount']]

        db[['in', 'out', 'amount', 'minamount', 'maxamount']] = db[['in', 'out', 'amount', 'minamount',
                                                                    'maxamount']].astype(float)
        db['course'] = db['out'] / db['in']
        # saving DataFrame to .CSV, later this can be saved to SQL DataBase
        db.to_csv(PATH_CURRENCIES, index=False)

        print('Updated successfully')

        timestamp = str(datetime.datetime.now().strftime(DATEFORMAT))

        # writing log-files
        DB.write_log(timestamp, 'DB updated', 'db')

        if archive:
            DB.archive_db(db)
            # writing log-files
            DB.write_log(timestamp, 'DB archived', 'db')

        else:
            pass

    @staticmethod
    def archive_db(database):
        print('Archiving database')
        try:
            temp = pd.read_csv(PATH_ARCHIVE_CURRENCIES)
        except FileNotFoundError:
            print('Database not found. It will be created in /data/ folder')
            temp = pd.DataFrame(columns=COLUMNS)
        temp = pd.concat([temp, database], axis=0)
        temp.to_csv(PATH_ARCHIVE_CURRENCIES, index=False)
        print('Archived successfully')

    def search(self, from_, to_, amount_, use_archived=True):
        if use_archived:
            self.db = pd.read_csv(PATH_CURRENCIES)
        else:
            pass
        timestamp = str(datetime.datetime.now().strftime(DATEFORMAT))
        log_string = str(from_) + ',' + str(to_) + ',' + str(amount_) + '\n'
        DB.write_log(timestamp, log_string, 'search')

        temp_db = self.db
        temp_db['new_amount'] = temp_db['course'] * amount_
        response = temp_db[(temp_db['from'] == from_) &
                           (temp_db['to'] == to_) &
                           (temp_db['new_amount'] <= temp_db['amount']) &
                           (temp_db['minamount'] <= amount_) &
                           (temp_db['maxamount'] >= amount_)]
        response = response.sort_values(by=['course'], ascending=False)
        self.response = response
        return response[['timestamp', 'www', 'from', 'to', 'course', 'new_amount']]

print('Curriencies database initialised')