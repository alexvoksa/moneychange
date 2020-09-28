import requests
import pandas as pd
import datetime
from lxml import objectify


class DB:
    def __init__(self):
        self.links = pd.read_csv('../data/links.csv', header=None)
        self.cols = ['timestamp', 'www', 'from', 'to', 'in', 'out', 'amount',
                     'fromfee', 'tofee', 'minamount', 'maxamount', 'param']
        self.db = pd.DataFrame(columns=self.cols)
        self.names_curr = pd.read_csv('../data/all_curr.csv')
        self.response = None

    @staticmethod
    def xml2df(link_):
        www = link_.split('/')[2]
        timestamp = str(datetime.datetime.now().strftime("%d:%m:%Y_%H:%M:%S"))
        text_response = requests.get(link_).text.encode()
        xml = objectify.fromstring(text_response)
        main_tree = xml.getroottree().getroot()
        full_list = []
        for i in main_tree.getchildren():
            dict_ = {j.tag: j.text for j in i.getchildren()}
            temp_df = pd.DataFrame([list(dict_.values())], columns=list(dict_.keys()))
            full_list.append(temp_df)
        super_xml = pd.concat(full_list, axis=0, ignore_index=True)
        super_xml['www'] = [www for i in range(len(super_xml))]
        super_xml['timestamp'] = [timestamp for i in range(len(super_xml))]
        return super_xml

    def update_db(self):
        print('Updating database...')
        for i in self.links[0].tolist():
            df = DB.xml2df(i)
            self.db = pd.concat([self.db, df], axis=0, ignore_index=True)
        self.db['minamount'] = self.db['minamount'].astype(str)
        self.db['maxamount'] = self.db['maxamount'].astype(str)
        self.db['minamount'] = [i.split(' ')[0] if i is not None else None for i in self.db['minamount']]
        self.db['maxamount'] = [i.split(' ')[0] if i is not None else None for i in self.db['maxamount']]
        self.db[['www', 'from', 'to', 'fromfee', 'tofee', 'param']] = self.db[['www', 'from', 'to', 'fromfee',
                                                                               'tofee', 'param']].astype(str)
        self.db[['in', 'out', 'amount', 'minamount', 'maxamount']] = self.db[['in', 'out', 'amount', 'minamount',
                                                                              'maxamount']].astype(float)
        self.db['course'] = self.db['out'] / self.db['in']
        self.db.to_csv('../data/currencies.csv', index=False)
        print('Updated successfully')
        self.archive_db()

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

    def search(self, from_, to_, amount_):
        temp_db = self.db
        temp_db['new_amount'] = temp_db['course'] * amount_
        response = temp_db[(temp_db['from'] == from_) & (temp_db['to'] == to_) & (temp_db['new_amount'] <= amount_) &
                           (amount_ >= temp_db['minamount']) & (temp_db['maxamount'] >= amount_)]
        response = response.sort_values(by=['course'], ascending=False).head(10)
        self.response = response
        print(response[['www', 'from', 'to', 'course', 'new_amount']])
