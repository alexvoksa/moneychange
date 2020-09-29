import requests
import pandas as pd
import datetime
from lxml import objectify
from tqdm import tqdm
import time


class DB:
    def __init__(self):
        self.links = pd.read_csv('../data/links.csv', header=None)
        # column list could be extended manually
        self.cols = ['timestamp', 'www', 'from', 'to', 'in', 'out', 'amount',
                     'fromfee', 'tofee', 'minfee', 'city', 'minamount', 'maxamount', 'param']
        self.db = pd.DataFrame(columns=self.cols)
        self.names_curr = pd.read_csv('../data/all_curr.csv')
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
            path = '../data/user_logs.txt'
        elif log == 'search':
            path = '../data/search_logs.txt'
        elif log == 'db':
            path = '../data/logs.txt'
        else:
            path = input('Paste correct path to log file')

        with open(path, 'a') as f:
            f.write(str(time_) + ',' + text + '\n')

    def xml2df(self, link_):
        super_xml = pd.DataFrame(columns=self.cols)
        # getting web-adress of site
        www = link_.split('/')[2]
        timestamp = str(datetime.datetime.now().strftime("%d:%m:%Y_%H:%M:%S"))

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

    def update_db(self, archive=False):
        # This method can update current database and archive (append it) to a CSV-file
        print('Updating database...')
        self.db = pd.DataFrame(columns=self.cols)
        for i in tqdm(self.links[0].tolist()):
            df = self.xml2df(i)
            self.db = pd.concat([self.db, df], ignore_index=True)
        # some currencies comes with currency name, for example 100 USD
        # these two list comprehensives removes currency name from DataFrame
        self.db['minamount'] = [i.split(' ')[0] if type(i) == str else i for i in self.db['minamount']]
        self.db['maxamount'] = [i.split(' ')[0] if type(i) == str is not None else i for i in self.db['maxamount']]

        self.db[['in', 'out', 'amount', 'minamount', 'maxamount']] = self.db[['in', 'out', 'amount', 'minamount',
                                                                              'maxamount']].astype(float)
        self.db['course'] = self.db['out'] / self.db['in']

        # saving DataFrame to .CSV, later this can be saved to SQL DataBase
        self.db.to_csv('../data/currencies.csv', index=False)

        print('Updated successfully')

        timestamp = str(datetime.datetime.now().strftime("%d:%m:%Y_%H:%M:%S"))

        # writing log-files
        DB.write_log(timestamp, 'DB updated', 'db')

        if archive:
            self.archive_db()
            # writing log-files
            DB.write_log(timestamp, 'DB archived', 'db')

        else:
            pass

    def archive_db(self):
        print('Archiving database')
        try:
            temp = pd.read_csv('../data/archive_currencies.csv')
        except FileNotFoundError:
            print('Database not found. It will be created in /data/ folder')
            temp = pd.DataFrame(columns=self.cols)
        temp = pd.concat([temp, self.db], axis=0)
        temp.to_csv('../data/archive_currencies.csv', index=False)
        print('Archived successfully')

    def search(self, from_, to_, amount_, use_archived=True):
        if use_archived:
            self.db = pd.read_csv('../data/currencies.csv')
        else:
            pass
        timestamp = str(datetime.datetime.now().strftime("%d:%m:%Y_%H:%M:%S"))
        log_string = str(from_) + ',' + str(to_) + ',' + str(amount_) + '\n'
        DB.write_log(timestamp, log_string, 'search')

        temp_db = self.db
        temp_db['new_amount'] = temp_db['course'] * amount_
        response = temp_db[(temp_db['from'] == from_) &
                           (temp_db['to'] == to_) &
                           (temp_db['new_amount'] <= temp_db['amount']) &
                           (temp_db['minamount'] <= amount_) &
                           (temp_db['maxamount'] >= amount_)]
        response = response.sort_values(by=['course'], ascending=False).head(10)
        self.response = response
        return response[['timestamp', 'www', 'from', 'to', 'course', 'new_amount']]
