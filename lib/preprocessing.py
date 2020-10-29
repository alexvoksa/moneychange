import pandas as pd
import numpy as np
from lib.Verification import UserCheck
import re
from datetime import datetime
import time

OUTPUT_STRING = 'Результаты проверки: \n\n' \
                'Кошелек {}\n' \
                'Сделано {} обменов\n' \
                'Число получателей: {}.\n' \
                'Количество успешных операций: {}\n' \
                'Количество неуспешных операций: {}\n' \
                '\n' \
                'Сводная статистика:\n' \
                'Вероятность использования ложного ФИО: {}%\n' \
                'Среднее число имен получателей: {}\n' \
                'Метрика активности клиента: {}%\n' \
                'Полнота контактных данных: {}%\n' \
                'Вероятность использования VPN: {}%\n' \
                'Средний чек одного обмена {}$'

OUTPUT_NONE_STRING = 'Данные по пользователю {} не обнаружены в системе.\n' \
                     'Вы можете помочь проекту отправив данные об обмене на {}'


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

    @staticmethod
    def count_active_time(time_field):
        # Getting amount of active days (longest interval between transactions)
        first_activity = datetime.strptime(time_field[0], '%Y/%m/%d')
        last_activity = datetime.strptime(time_field[-1], '%Y/%m/%d')
        days_active = (last_activity - first_activity).days
        if days_active == 0:
            days_active = 1
        else:
            pass
        return days_active

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

            phone = Preprocessor.leave_digits(str(phone))  # +

            dollar_amount = Preprocessor.dollar_equivalent(self.course_dict, amount_in, currency_id)  # +
            from_name, to_name, skype = str(from_name).lower(), str(to_name).lower(), str(skype).lower()  # +

            time_ = '/'.join([str(time_.year), str(time_.month), str(time_.day)])  # +

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
        return wallets_dict

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
        return wallets_dict

    def __count_metrics(self, wallets_dict):
        """
        This function updates dictionary.
        It can compute necessary metrics and update dictionary
        """
        wallets_from = list(wallets_dict.keys()).copy()

        # amount of different senders per one sender wallet filled by customer
        for key_from in wallets_from:
            contacts_from_amount = len(wallets_dict[key_from]['from_name'])
            # quantity of linked wallets, except other parameters like dollar amount, mean metrics etc.
            wallets_dict[key_from]['sender_names_amount'] = contacts_from_amount

            # Lists for counted metrics
            # Metrics will be appended on every iteration
            mean_contacts_metric = []
            mean_ip_metric = []
            mean_activity_metric = []
            mean_receiver_names_metric = []

            # Wallets to list
            wallets_to = list(wallets_dict[key_from].keys()).copy()

            exceptions_list_from = ['from_name', 'dollar_total', 'total_exodus', 'total_operations',
                                    'accepted_operations', 'rejected_operations', 'sender_names_amount']
            wallets_to = [key for key in wallets_to if key not in exceptions_list_from]
            wallets_to_amount = len(wallets_to)

            for key_to in wallets_to:
                names_to_amount = len(wallets_dict[key_from][key_to]['to_name'])
                exoduses_amount = len(wallets_dict[key_from][key_to]['exodus'])
                exodus_positive = sum(wallets_dict[key_from][key_to]['exodus'])

                # amount of active days when operations were made to receiver wallet
                days_active = Preprocessor.count_active_time(wallets_dict[key_from][key_to]['time'])

                # frequency of operations per days of activity
                activity_metric = Preprocessor.count_metric(exoduses_amount, days_active)
                # amount of positive exoduses divided by exoduses amount
                relative_positive_exoduses = Preprocessor.count_metric(exodus_positive, exoduses_amount)
                # quantity of unique receivers (names) for one wallet-receiver divided by amount of operations
                relative_names_metric = Preprocessor.count_metric(names_to_amount, wallets_to_amount)
                # quantity of unique emails for one wallet-receiver divided by amount of operations
                relative_email_metric = Preprocessor.count_metric(wallets_dict[key_from][key_to]['unique_email'],
                                                                  exoduses_amount)
                # quantity of unique phones for one wallet-receiver divided by amount of operations
                relative_phone_metric = Preprocessor.count_metric(wallets_dict[key_from][key_to]['unique_phone'],
                                                                  exoduses_amount)
                # quantity of unique skype for one wallet-receiver divided by amount of operations
                relative_skype_metric = Preprocessor.count_metric(wallets_dict[key_from][key_to]['unique_skype'],
                                                                  exoduses_amount)
                # quantity of unique messengers for one wallet-receiver divided by amount of operations
                relative_messenger_metric = Preprocessor.count_metric(
                    wallets_dict[key_from][key_to]['unique_messenger'],
                    exoduses_amount)
                # Less different IP's better. VPN and proxy metric. Best == 0, worst == 1
                relative_ip_metric = Preprocessor.count_metric(wallets_dict[key_from][key_to]['unique_ip'],
                                                               exoduses_amount)
                # Less different countries is better. VPN and proxy metric. Best == 1, worst == 0
                relative_country_metric = Preprocessor.count_metric(wallets_dict[key_from][key_to]['unique_country'],
                                                                    exoduses_amount)
                # Less different cities is better. VPN and proxy metric. Best == 0, worst == 1
                relative_city_metric = Preprocessor.count_metric(wallets_dict[key_from][key_to]['unique_city'],
                                                                 exoduses_amount)

                # Adding counted metrics to recipients wallets
                metric_names = ['names_metric', 'email_metric', 'phone_metric', 'skype_metric', 'messenger_metric',
                                'ip_metric', 'country_metric', 'city_metric', 'exodus_metric', 'activity_metric',
                                'days_active']
                metrics = [relative_names_metric, relative_email_metric, relative_phone_metric, relative_skype_metric,
                           relative_messenger_metric, relative_ip_metric, relative_country_metric, relative_city_metric,
                           relative_positive_exoduses, activity_metric, days_active]
                for metric_name, metric in zip(metric_names, metrics):
                    wallets_dict[key_from][key_to].update({metric_name: metric})

                # Add name metric to mean_receiver_names_metric
                mean_receiver_names_metric.append(relative_names_metric)
                # Adding contacts metrics to mean_contacts_metric
                for contact_metric in [relative_email_metric, relative_phone_metric,
                                       relative_skype_metric, relative_messenger_metric]:
                    mean_contacts_metric.append(contact_metric)

                # Adding IP, Country, City to mean_ip_metric
                # for ip_metric in [relative_ip_metric, relative_country_metric, relative_city_metric]: # !!!
                #    mean_ip_metric.append(ip_metric)
                # ||
                # \/  This is a VPN metric. More different countries == More VPN probability
                mean_ip_metric.append(1 - relative_country_metric)

                # Adding activity metric to mean activity metrics
                mean_activity_metric.append(wallets_dict[key_from][key_to]['activity_metric'])

            mean_receiver_names_metric = np.mean(mean_receiver_names_metric)
            mean_contacts_metric = np.mean(mean_contacts_metric)
            mean_ip_metric = np.mean(mean_ip_metric)
            mean_activity_metric = np.mean(mean_activity_metric)

            wallets_dict[key_from]['number_of_receivers'] = wallets_to_amount
            wallets_dict[key_from]['mean_receiver_names_metric'] = mean_receiver_names_metric
            wallets_dict[key_from]['mean_contacts_metric'] = mean_contacts_metric

            # VPN metric
            wallets_dict[key_from]['mean_ip_metric'] = mean_ip_metric
            # amount of operations per day
            wallets_dict[key_from]['mean_activity_metric'] = mean_activity_metric
            # quantity metric of different wallets that receive money
            #
            # amount of sender names divided by number of receivers
            # Metric for using fake name
            wallets_dict[key_from]['sender_names_metric'] = 1 - wallets_dict[key_from]['sender_names_amount'] / \
                                                            wallets_to_amount
            # dollar amount per operation
            wallets_dict[key_from]['relative_dollar_metric'] = wallets_dict[key_from]['dollar_total'] / \
                                                               wallets_dict[key_from]['total_operations']
        self.wallets_dict = wallets_dict
        return wallets_dict

    def check_user(self, wallet_id):
        wallet_id = str(wallet_id)
        print(OUTPUT_STRING.format(wallet_id,
                                   str(self.wallets_dict[wallet_id]['total_operations']),
                                   str(self.wallets_dict[wallet_id]['number_of_receivers']),
                                   str(self.wallets_dict[wallet_id]['accepted_operations']),
                                   str(self.wallets_dict[wallet_id]['rejected_operations']),
                                   str(round(self.wallets_dict[wallet_id]['sender_names_metric']*100, 2)),
                                   str(round(self.wallets_dict[wallet_id]['mean_receiver_names_metric'])),
                                   str(round(self.wallets_dict[wallet_id]['mean_activity_metric']*100, 2)),
                                   str(round(self.wallets_dict[wallet_id]['mean_contacts_metric']*100, 2)),
                                   str(round(self.wallets_dict[wallet_id]['mean_ip_metric']*100, 2)),
                                   str(round(self.wallets_dict[wallet_id]['relative_dollar_metric'], 2))
                                   )
              )

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
        self.__count_metrics(self.__count_amounts(self.__generate_wallets_dict(*data_columns)))
        random_id = np.random.randint(0, len(self.wallets_dict))
        wallet_key = list(self.wallets_dict.keys())[random_id]
        self.check_user(wallet_key)


a = Preprocessor()
a.generate_data()

print('Ho-ho')
