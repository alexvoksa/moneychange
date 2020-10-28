import pandas as pd
import numpy as np
from lib.Verification import UserCheck
import re
from datetime import datetime
import time


class Preprocessor:
    def __init__(self):
        self.path_to_money_db = '../data/Verification/_courses.csv'
        self.path_to_main_df = '../data/Verification/com_operations_with_head.csv'
        self.main_dataframe = pd.read_csv(self.path_to_main_df)
        self.money_db = pd.read_csv(self.path_to_money_db)  # columns = ['id', 'name', 'short_name', 'real_rate_to_usd']
        self.course_dict = {str(i): str(k) for (i, k) in zip(self.money_db['id'],
                                                             self.money_db['real_rate_to_usd'])}
        self.wallets_dict = None
        self.parameters_list = ['email', 'to_name', 'phone', 'skype', 'messenger', 'ip',
                                'country', 'city', 'time', 'dollars_amount', 'exodus']

    @staticmethod
    def dollar_equivalent(database_dictionary, amount_in, currency_id):
        try:
            dollar_course = database_dictionary[str(currency_id)]
            dollar_course = dollar_course.replace(',', '.')
            dollar_course = float(dollar_course)
        except KeyError:
            dollar_course = 0.0
        return float(amount_in) * dollar_course

    @staticmethod
    def sigmoid(x):
        return 1 / (1 + np.exp(-x))

    @staticmethod
    def getdate(i):
        date = datetime.strptime(i, '%Y-%m-%d %H:%M:%S')
        return date

    @staticmethod
    def is_null(value):
        if isinstance(value, str):
            if len(value) > 3:
                return True
            else:
                return False
        else:
            return False

    @staticmethod
    def remove_empty_element(var):
        for char in ['nan', None, '', ' ', np.nan]:
            while char in var:
                var.remove(char)
        return var

    @staticmethod
    def leave_digits(line):
        new_line = []
        for char in line:
            if char.isdigit():
                new_line.append(char)
            else:
                pass
        line = ''.join(new_line)
        return line

    @staticmethod
    def drop_duplicates(line):
        return list(set(line))

    @staticmethod
    def count_metric(category, total):
        if total == 0:
            result = 0
        else:
            result = category / total
        return round(result, 4)

    def __prepare_dataframe(self):
        data = self.main_dataframe.copy()
        if all(data.columns == ['id', 'user_id', 'sys_from', 'sys_to', 'amount_from', 'amount_to',
                                'course', 'from_st', 'to_st', 'from_name', 'to_name', 'from_id',
                                'to_id', 'z_time', 'pay_time', 'cancel_time', 'confirm_time',
                                'transaction_number', 'c_time', 'user_contacts', 'user_ip',
                                'user_email', 'partner_id', 'partner_coeff', 'cancel_comment',
                                'uniq_id', 'success', 'idx']):
            data = data[[isinstance(i, str) for i in data['user_ip']]]
            data['income_time'] = data['z_time'].apply(Preprocessor.getdate)

            """
            This cycle gets data from incoming time amd final time and appends True/False to three lists
            """
            exodus_status = []
            exodus_time = []
            reconfirmation = []
            for cancel, confirm in zip(data['cancel_time'], data['c_time']):
                if cancel == '0000-00-00 00:00:00' and confirm != '0000-00-00 00:00:00':
                    exodus_time.append(confirm)
                    exodus_status.append(True)
                    reconfirmation.append(False)

                elif cancel != '0000-00-00 00:00:00' and confirm == '0000-00-00 00:00:00':
                    exodus_time.append(cancel)
                    exodus_status.append(False)
                    reconfirmation.append(False)

                else:
                    exodus_time.append(confirm)
                    exodus_status.append(True)
                    reconfirmation.append(True)

            data['exodus_time'] = exodus_time
            data['exodus_time'] = data['exodus_time'].apply(Preprocessor.getdate)
            data['reconfirmation'] = reconfirmation
            data['exodus_status'] = exodus_status

            data['income_hour'] = [i.hour for i in data['income_time']]
            data['income_minute'] = [i.minute for i in data['income_time']]
            data['income_month'] = [i.month for i in data['income_time']]
            data['income_year'] = [i.year for i in data['income_time']]

            data['exodus_hour'] = [i.hour for i in data['exodus_time']]
            data['exodus_minute'] = [i.minute for i in data['exodus_time']]
            data['exodus_month'] = [i.month for i in data['exodus_time']]
            data['exodus_year'] = [i.year for i in data['exodus_time']]

            data['cancel_comment'] = data['cancel_comment'].apply(Preprocessor.is_null).astype(bool)

            data['customer_city'], data['customer_country'], \
            data['geoname_id'], data['threat'] = UserCheck.get_info_from_ip(data['user_ip'])

            data['conn_is_anonimous'] = [i.autonomous_system_number if not isinstance(i, float) else False for i in
                                         data['threat']]
            data['conn_is_anonimous_proxy'] = [i.is_anonymous_proxy if not isinstance(i, float) else False for i in
                                               data['threat']]
            data['conn_is_anonimous_vpn'] = [i.is_anonymous_vpn if not isinstance(i, float) else False for i in
                                             data['threat']]
            data['conn_is_satellite_provider'] = [i.is_satellite_provider if not isinstance(i, float) else False for i
                                                  in
                                                  data['threat']]
            data['conn_is_tor_exit_node'] = [i.is_tor_exit_node if not isinstance(i, float) else False for i in
                                             data['threat']]

            data['email'], data['phone'], \
            data['skype'], data['icq'] = UserCheck.get_contacts(data['user_contacts'], r'<br>')

            data['phone'] = data['phone'].apply(lambda x: x.replace(' ', ''))
            data['to_crypto'] = [True if (i == 32) or (i == 35) else False for i in data['sys_to']]

            data.drop(['from_id', 'to_id', 'z_time', 'pay_time', 'cancel_time', 'confirm_time', 'c_time',
                       'transaction_number', 'user_contacts', 'user_email', 'uniq_id', 'success', 'idx',
                       'threat'], axis=1, inplace=True)
            data = data[[not np.isnan(i) if isinstance(i, float) else True for i in data['from_st']]].copy()
            data.index = [i for i in range(len(data))]
        else:
            print('DataFrame not properly constructed! Wrong columns! \n'
                  'nesessary columns:\n'
                  '[id, user_id, sys_from, sys_to, amount_from, amount_to, course, from_st, to_st, from_name,\n'
                  'to_name, from_id,to_id, z_time, pay_time, cancel_time, confirm_time, transaction_number,\n'
                  'c_time, user_contacts, user_ip, user_email, partner_id, partner_coeff, cancel_comment,\n'
                  'uniq_id, success, idx]\n')
            raise
        self.main_dataframe = data

    def __generate_wallets_dict(self, wallet_from_id_array, email_array, wallet_to_id_array, name_from_array,
                                name_to_array, phone_array, skype_array, messenger_array, ip_array, country_array,
                                city_array, time_array, exodus_array, amount_in_array, currency_id_array):
        """
        Baseline wallet structure looks like
        wallet_from: {wallet_to: {'email': [email],
                                  'to_name': [to_name],
                                  'phone': [phone],
                                  'skype': [skype],
                                  'messenger': [messenger],
                                  'ip': [ip],
                                  'country': [country],
                                  'city': [city],
                                  'time': [time],
                                  'dollar_amount': [dollar_amount],
                                  'exodus': [exodus]
                                  }
                      }
        """
        wallets_dict = {}
        for wallet_from, email, wallet_to, from_name, to_name, phone, skype, messenger, ip, country, city, time_, \
            exodus, amount_in, \
            currency_id in zip(wallet_from_id_array, email_array, wallet_to_id_array, name_from_array,
                               name_to_array, phone_array, skype_array, messenger_array,
                               ip_array, country_array, city_array,
                               time_array,
                               exodus_array, amount_in_array, currency_id_array):

            phone = Preprocessor.leave_digits(str(phone)) # +

            dollar_amount = Preprocessor.dollar_equivalent(self.course_dict, amount_in, currency_id) # +
            from_name, to_name, skype = str(from_name).lower(), str(to_name).lower(), str(skype).lower() # +

            time_ = '/'.join([str(time_.year), str(time_.month), str(time_.day)]) # +

            sub_wallet_values = [email, to_name, phone, skype, messenger, ip,
                                 country, city, time_, dollar_amount, exodus]
            try:
                if wallets_dict[wallet_from]:
                    wallets_dict[wallet_from]['from_name'].append(from_name)
                    try:
                        if wallets_dict[wallet_from][wallet_to]:
                            for key, value in zip(self.parameters_list, sub_wallet_values):
                                wallets_dict[wallet_from][wallet_to][key].append(value)
                    except KeyError:
                        updater = {wallet_to: {key: [value] for key, value in zip(self.parameters_list,
                                                                                  sub_wallet_values)}}
                        wallets_dict[wallet_from].update(updater)
                else:
                    print('Err')
            except KeyError:
                updater = {wallet_to: {key: [value] for key, value in zip(self.parameters_list, sub_wallet_values)}}
                wallets_dict[wallet_from] = {'from_name': [from_name]}
                wallets_dict[wallet_from].update(updater)

        self.wallets_dict = wallets_dict

    def __count_amounts(self, wallets_dict):
        for key_from in wallets_dict.keys():
            wallets_dict[key_from]['from_name'] = Preprocessor.drop_duplicates(wallets_dict[key_from]['from_name'])
            wallets_dict[key_from]['from_name'] = Preprocessor.remove_empty_element(wallets_dict[key_from]['from_name'])

            wallets_dict[key_from]['dollar_total'] = []

            wallets_dict[key_from]['total_exodus'] = []

            for key_to in wallets_dict[key_from].keys():
                if key_to not in ['from_name', 'dollar_total', 'total_exodus', 'unique_email', 'unique_to_name',
                                  'unique_phone', 'unique_skype', 'unique_messenger', 'unique_ip',
                                  'unique_country', 'unique_city']:

                    quantity_sub_keys_list = ['unique_email', 'unique_to_name', 'unique_phone', 'unique_skype',
                                              'unique_messenger', 'unique_ip', 'unique_country', 'unique_city']

                    sub_keys_list = ['email', 'to_name', 'phone', 'skype', 'messenger', 'ip', 'country', 'city']

                    print(key_to)
                    for sub_key, quantity in zip(sub_keys_list, quantity_sub_keys_list):
                        wallets_dict[key_from][key_to][sub_key] = \
                            Preprocessor.drop_duplicates(wallets_dict[key_from][key_to][sub_key])
                        wallets_dict[key_from][key_to][sub_key] = \
                            Preprocessor.remove_empty_element(wallets_dict[key_from][key_to][sub_key])
                        # this block stands for generating amount(len) of unique metrics per recipient wallet
                        # for example - unique email or human names
                        wallets_dict[key_from][key_to].update({quantity: len(wallets_dict[key_from][key_to][sub_key])})

                    # As dict was created earlier, there are three keys, that have no sub-dicts
                    # as a result, cycle must avoid use them
                    wallets_dict[key_from]['total_exodus'].extend(wallets_dict[key_from][key_to]['exodus'])
                    wallets_dict[key_from]['dollar_total'].extend(wallets_dict[key_from][key_to]['dollars_amount'])
                else:
                    pass

            # add comment
            total_operations = len(wallets_dict[key_from]['total_exodus'])
            accepted_operations = sum(wallets_dict[key_from]['total_exodus'])
            rejected_operations = total_operations - accepted_operations
            # add comment
            wallets_dict[key_from]['total_operations'] = total_operations
            wallets_dict[key_from]['accepted_operations'] = accepted_operations
            wallets_dict[key_from]['rejected_operations'] = rejected_operations
            # add comment
            wallets_dict[key_from]['dollar_total'] = sum(wallets_dict[key_from]['dollar_total'])

        self.wallets_dict = wallets_dict

    def generate_data(self):
        self.__prepare_dataframe()
        data_columns = [self.main_dataframe['from_st'],
                        self.main_dataframe['email'],
                        self.main_dataframe['to_st'],
                        self.main_dataframe['from_name'],
                        self.main_dataframe['to_name'],
                        self.main_dataframe['phone'],
                        self.main_dataframe['skype'],
                        self.main_dataframe['icq'],
                        self.main_dataframe['user_ip'],
                        self.main_dataframe['customer_country'],
                        self.main_dataframe['customer_city'],
                        self.main_dataframe['income_time'],
                        self.main_dataframe['exodus_status'],
                        self.main_dataframe['amount_from'],
                        self.main_dataframe['sys_from']]
        self.__generate_wallets_dict(*data_columns)
        self.__count_amounts(self.wallets_dict)



a = Preprocessor()
a.generate_data()

print(a.wallets_dict[list(a.wallets_dict.keys())[0]])
print('Ho-ho')