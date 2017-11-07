import datetime
import os
import sys
import time

import urllib3
import vk_api

from beauty_neural_correct.settings import TOKEN, logger
from bot.utils.SearchUtils import SearchUtils
from bot.utils.TestUtils import TestUtils

urllib3.disable_warnings()

vk_session = vk_api.VkApi(token=TOKEN)

with open(os.path.join(os.path.dirname(sys.argv[0]),
                       'settings_dir/loginpassword.txt'),
          'r') as auth_data:
    login = str(auth_data.readline()).split('=')[1].replace('\n', '', 1)
    password = str(auth_data.readline()).split('=')[1].replace('\n', '', 1)
user_vk_session = vk_api.VkApi(login=login, password=password)
user_vk_session.auth()


def get_some_settings_file_content(file_name):
    with open(os.path.join(os.path.dirname(sys.argv[0]),
                           'settings_dir/{}.txt'.format(file_name)),
              'r', encoding='utf-8') as file:
        return file.read()


def main():
    global item
    values = {'out': 0, 'count': 100, 'time_offset': 60}
    vk_session.method('messages.get', values)
    while True:
        try:
            response = vk_session.method('messages.get', values)
            if response['items']:
                values['last_message_id'] = response['items'][0]['id']
            for item in response['items']:
                if item['body'] == 'остановить поиск':
                    continue

                if get_some_settings_file_content('selected_mode') == 'test':
                    test_utils = TestUtils(
                        message=str(item['body']).lower(),
                        suter_user_id=item['user_id'],
                        item=item, vk_session=vk_session,
                        selected_set=get_some_settings_file_content('selected_set')
                    )
                    test_utils.testing_message_handler()
                else:
                    search_utils = SearchUtils(
                        vk_session=vk_session,
                        user_vk_session=user_vk_session,
                        suter_user_id=item['user_id'],
                        selected_set=get_some_settings_file_content('selected_set'),
                        minimum_difference=get_some_settings_file_content('difference'),
                        message=str(item['body']).lower(),
                        item=item
                    )
                    search_utils.search_message_handler()

            time.sleep(1)
        except Exception as ex:
            logger.error('In main: ' + str(ex))
            vk_session.method('messages.send', {
                'user_id': item['user_id'],
                'message': 'Выполнение команды было экстренно завершено'
            })


if __name__ == '__main__':
    main()
