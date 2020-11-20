import pandas as pd
import numpy as np
import re
from datetime import datetime
import time
from tqdm import tqdm
import geoip2.database
import requests
from bs4 import BeautifulSoup


IP_DATABASE_PATH = '../data/Verification/databases_max/GeoLite2-City.mmdb'
GEO_COLUMNS = ['ip', 'city', 'country', 'id', 'threats']
CHECKER_WEB_PATH = 'https://www.neberitrubku.ru/nomer-telefona/{}'
CONTACTS_COLUMNS = ['email', 'phone', 'skype', 'icq']


class UserCheck:
    @staticmethod
    def get_info_from_ip(ip_source_series):
        """
        this function gets information from ip-string
        It uses geoip2 library and IP-database, made specially for this library
        It returns 4 lists:  customer_city, customer_country, geo_name_id, threats
        and updates a DataFrame with geo-data, that stores in class instance
        """
        with geoip2.database.Reader(IP_DATABASE_PATH) as reader:
            customer_city = []
            customer_country = []
            threats = []
            geo_name_id = []
            for i in ip_source_series:
                try:
                    if isinstance(i, str):
                        response = reader.city(i)
                        customer_city.append(response.city.name)
                        customer_country.append(response.country.name)
                        threats.append(response.traits)
                        geo_name_id.append(response.city.geoname_id)
                    else:
                        customer_city.append(np.nan)
                        customer_country.append(np.nan)
                        threats.append(np.nan)
                        geo_name_id.append(np.nan)

                except Exception:
                    customer_city.append(np.nan)
                    customer_country.append(np.nan)
                    threats.append(np.nan)
                    geo_name_id.append(np.nan)
        return customer_city, customer_country, geo_name_id, threats

    @staticmethod
    def get_contacts(user_contacts, delimiter):
        """
        this function get phone skype email and messenger(icq/telegram) from string
        contacts are divided by <br>
        It returns 4 lists: email, phone, skype, icq and updates a DataFrame with contacts,
        that stores in class instance
        """
        email = []
        phone = []
        skype = []
        icq = []

        database = [re.split(delimiter, str(i)) for i in user_contacts]
        for j in database:
            counter = 0
            for k in j:
                if 'Phone:' in k:
                    phone.append(k.replace('Phone: ', ''))
                elif 'Skype:' in k:
                    skype.append(k.replace('Skype: ', ''))
                elif 'ICQ:' in k:
                    icq.append(k.replace('ICQ: ', ''))
                elif 'Email:' in k:
                    email.append(k.replace('Email: ', ''))
                    counter += 2
                elif k == 'nan' and len(j) == 1:
                    phone.append(k)
                    skype.append(k)
                    icq.append(k)
                    email.append(k)
                    counter += 1
                else:
                    print('check for errors')
            if counter == 0:
                email.append(np.nan)
        return email, phone, skype, icq

    @staticmethod
    def check_phone(phone_number_string, recall_limit):
        """
        Function stands for recognizing untrusted phone number in contacts data

        """
        while ' ' in phone_number_string:
            phone_number_string = str(phone_number_string).replace(' ', '')
        response = requests.get(CHECKER_WEB_PATH.format(phone_number_string))
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            try:
                answer_str = soup.find_all('article')[0].div.get_text('|', strip=True).split('|')
            except AttributeError:
                answer_dict = {'number': phone_number_string,
                               'other': 'No data'
                               }
                return answer_dict

            answer_len = len(answer_str)
            if answer_len > 6:
                answer_dict = {'number': answer_str[0],
                               'rating_category': answer_str[1].split(' ', maxsplit=1)[0],
                               'caller_type': answer_str[1].split(' ', maxsplit=1)[1],
                               'number_type': answer_str[2],
                               'country': answer_str[3],
                               'first': answer_str[5]
                               }

                if ('категории' in answer_str[6].lower()) or ('categories' in answer_str[6].lower()):
                    return answer_dict

                elif ('категории' in answer_str[7].lower()) or ('categories' in answer_str[7].lower()):
                    answer_dict.update({'second': answer_str[6]})
                    return answer_dict

                elif ('категории' in answer_str[8].lower()) or ('categories' in answer_str[8].lower()):
                    answer_dict.update({'second': answer_str[6], 'third': answer_str[7]})
                    return answer_dict

                else:
                    print(answer_str)

            else:
                answer_dict = {'number': answer_str[0],
                               'category': answer_str[1],
                               'other': 'No data'
                               }
                return answer_dict

        else:
            try:
                if answer_dict:
                    return answer_dict
            except NameError:
                if recall_limit != 0:
                    recall_limit -= 1
                    print('Wating 20 secs...')
                    time.sleep(20)
                    UserCheck.check_phone(phone_number_string, recall)
                else:
                    print('Try again later')
                    raise Exception

