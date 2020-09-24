import re
import requests
import pandas as pd


class DB:

    def __init__(self):
        self.links = pd.read_csv('data/links.csv', header=None)
        self.cols = ['www', 'from', 'to', 'in', 'out', 'amount',
                     'fromfee', 'tofee', 'minamount', 'maxamount', 'param']
        self.db = pd.DataFrame(columns=self.cols)
        self.response = None

    def parse_xml(self, link_):
        text_response = requests.get(link_).text
        www = link_.split('/')[2]
        pd_col = []
        for col_name in self.cols[1:]:
            match = re.compile('[<]{}[>].+[<]/{}[>]'.format(col_name, col_name))
            match_values = match.findall(text_response)
            if len(match_values) == 0 and len(pd_col) > 0:
                final_values = tuple([None for i in range(len(pd_col[-1]))])
            else:
                final_values = tuple([i.replace('<{}>'.format(col_name), '').replace('</{}>'.format(col_name), '')
                                      for i in match_values])
            pd_col.append(final_values)
        pd_col.insert(0, tuple([www for i in range(len(pd_col[0]))]))
        df = pd.DataFrame(pd_col).T
        df.columns = self.cols
        self.db = pd.concat([self.db, df], axis=0)
        self.db['minamount'] = [str(i).split(' ')[0] if i is not None else None for i in self.db['minamount']]
        self.db['maxamount'] = [str(i).split(' ')[0] if i is not None else None for i in self.db['maxamount']]
        self.db[['www', 'from', 'to', 'fromfee', 'tofee', 'param']] = self.db[
            ['www', 'from', 'to', 'fromfee', 'tofee', 'param']].astype(str)
        self.db[['in', 'out', 'amount', 'minamount', 'maxamount']] = self.db[
            ['in', 'out', 'amount', 'minamount', 'maxamount']].astype(float)
        self.db['course'] = self.db['out'] / self.db['in']

    def update_db(self):
        print('Updating database...')
        for i in self.links[0].tolist():
            self.parse_xml(i)
        self.db.to_csv('data/currencies.csv')
        print('Updated successfully')

    def search(self, from_, to_, amount_):
        temp_db = self.db
        temp_db['new_amount'] = temp_db['course']*amount_
        response = temp_db[(temp_db['from'] == from_) & (temp_db['to'] == to_) & (temp_db['new_amount'] <= amount_) &
                           (amount_ >= temp_db['minamount']) & (temp_db['maxamount'] >= amount_)]
        response = response.sort_values(by=['course'], ascending=False).head(10)
        self.response = response
        print(response[['www', 'from', 'to', 'course', 'new_amount']])


a = DB()

a.update_db()

money_from = str(input('Change from?'))
money_to = str(input('Change to?'))
money_amount = float(input('Amount?'))

a.search(money_from, money_to, money_amount)
