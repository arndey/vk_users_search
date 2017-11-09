import os
import random

import django
import numpy
import requests
import time

import sys
import vk_api
from skimage import io

from vk_users_search.settings import SETS_PATH_PREFIX, logger
from bot.messages_and_phrases import WHORE_PHRASES, SEARCHING_COMMANDS_MESSAGE
from bot.utils.CommonUtils import CommonUtils

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vk_users_search.settings')
django.setup()
from bot.models import UserData


class SearchUtils(CommonUtils):
    def __init__(self, vk_session, user_vk_session, suter_user_id,
                 selected_set, minimum_difference, message, item):
        super().__init__(vk_session, suter_user_id, message, item)
        self.vk_session = vk_session
        self.user_vk_session = user_vk_session
        self.suter_user_id = suter_user_id
        self.selected_set = selected_set
        self.minimum_difference = minimum_difference
        self.message = message
        self.item = item

    def is_girl_old_or_young(self, girl_user_id):
        bdate = self.vk_session.method('users.get', {
            'user_ids': girl_user_id,
            'fields': 'bdate, sex',
        })[0]['bdate']
        bdate_arr = bdate.split('.')
        if bdate_arr.__len__() == 3:
            birth_year = int(bdate_arr[2])
            if birth_year < 1996 or birth_year > 2004:
                return True

        return False

    def send_by_suitable(self, girl_user_id):
        upload = vk_api.VkUpload(self.vk_session)
        photo_data = upload.photo_messages('current_girl.jpg')
        self.send_message(message_to_send='vk.com/id' + str(girl_user_id),
                          attachment='photo{owner_id}_{media_id}'
                          .format(owner_id=int(photo_data[0]['owner_id']),
                                  media_id=photo_data[0]['id']))
        try:
            UserData(user_id=girl_user_id, suitable=True).save()
        except:
            pass

    def get_photos(self, girl_user_id):
        albums = self.user_vk_session.method('photos.getAlbums', {
            'owner_id': girl_user_id,
            'need_system': 1
        })['items']
        main_album = None
        for alb in albums:
            if str(alb['title']).__contains__('Фотографии со страницы'):
                main_album = alb
                break

        return self.user_vk_session.method('photos.get', {
            'owner_id': girl_user_id,
            'album_id': main_album['id'],
            'rev': 1,
            'count': 10
        })['items']

    def is_girl_suitable(self, photos, girl_user_id):
        try:
            if UserData.objects.filter(user_id=girl_user_id) \
                    .__len__() > 0:
                return False
        except:
            pass

        corrupt_photos = 0
        checked_photos = 0
        for photo in photos:
            bytes = requests.get(photo['photo_604']).content
            with open('current_girl.jpg', 'wb') as new:
                new.write(bytes)
            images = self.get_io_images(SETS_PATH_PREFIX + self.selected_set)
            for image in images:
                try:
                    current_score = self.get_beauty_score(
                        image[1], io.imread('current_girl.jpg'))
                except:
                    corrupt_photos += 1
                    break
                if current_score <= self.minimum_difference:
                    SearchUtils.send_by_suitable(self, girl_user_id)
                    return True
            else:
                checked_photos += 1
                if checked_photos >= 3:
                    UserData(user_id=girl_user_id, suitable=False).save()
                    return False

        UserData(user_id=girl_user_id, suitable=False).save()
        return False

    def is_girl_whore_or_bot(self, girl_user_id):
        entries = self.user_vk_session.method('wall.get', {
            'owner_id': girl_user_id,
            'count': '15'
        })['items']
        if entries.__len__() < 3:
            return True

        for entry in entries:
            try:
                if entry['views']['count'] < 100:
                    return True
            except:
                continue
        for entry in entries[0:5]:
            for phrase in WHORE_PHRASES:
                if str(entry['text']).lower().split(' ').__contains__(phrase):
                    return True

        return False

    def get_search_parameters(self):
        search_by = self.message['поиск по '.__len__():].split()[0].lower()
        number_of_result = self.message.split()[self.message.split().__len__() - 1]
        place_name = self.message[
                     str('поиск по ' + search_by).__len__():self.message.index(number_of_result)
                     ].strip().lower()

        return [search_by, place_name, number_of_result]

    def do_search(self, peoples, number_of_result):
        suitable_counter = 0
        not_suitable_counter = 0

        for people in peoples:
            girl_user_id = people['id']
            try:
                if self.is_girl_whore_or_bot(girl_user_id):
                    continue
                photos = self.get_photos(girl_user_id)
            except:
                continue

            if photos.__len__() < 2:
                continue
            last_message = self.vk_session.method('messages.get', {
                'count': 1
            })['items'][0]
            if last_message['user_id'] == self.suter_user_id and \
                            str(last_message['body']).lower() == 'остановить поиск':
                return -1

            try:
                is_girl_suitable_var = self \
                    .is_girl_suitable(girl_user_id, photos)
            except:
                continue
            if is_girl_suitable_var:
                suitable_counter += 1
                if suitable_counter >= int(number_of_result):
                    self.send_message('Поиск окончен, необходимое кол-во найдено')
                    return
            else:
                not_suitable_counter += 1
                if not_suitable_counter % 5 == 0:
                    self.send_message('Нейросетью отвергнуто {num} на данный момент'
                                      .format(num=not_suitable_counter))

    def search_by_city(self, city_name, number_of_result):
        def get_peoples(city_id, offset):
            peoples = []
            birth_years = numpy.random.permutation(list(range(1996, 2004)))
            birth_month = numpy.random.permutation(list(range(11)))

            for year in birth_years:
                for month in birth_month:
                    try:
                        current_peoples = self.user_vk_session.method('users.search', {
                            'sex': 1,
                            'city': city_id,
                            'sort': 1,
                            'count': 100,
                            'offset': offset,
                            'has_photo': 1,
                            'birth_year': year,
                            'birth_month': month
                        })['items']
                    except:
                        continue
                    peoples.extend(current_peoples)

            return peoples

        def get_city_id_by_name():
            for country in self.user_vk_session.method('database.getCountries')['items']:
                cities = self.user_vk_session.method('database.getCities', {
                    'country_id': country['id'],
                    'q': city_name
                })['items']
                for city in cities:
                    if city['title'].lower() == city_name.lower():
                        return city['id']
            else:
                return None

        city_id = get_city_id_by_name()
        if city_id is None:
            self.send_message('Данный город не найден')
            return

        offset = 900
        while offset >= 0:
            peoples = get_peoples(city_id, offset)
            if peoples.__len__() > 0:
                self.send_message('Первая часть страниц загрузилась')
            else:
                self.send_message('Страниц для сканирования не найдено')
                return

            self.do_search(peoples, number_of_result)
            offset -= 100
        self.send_message('Поиск выполнен, участники для проверки закончились')

    def search_by_group(self, search_parameters):
        def get_offset():
            if self.vk_session.method('groups.getMembers', {
                'group_id': group_id,
                'fields': 'sex, city',
                'offset': 1000000,
                'sort': 'id_desc'
            })['items'].__len__() > 900:
                return 100000 + random.randint(1000, 10000)
            elif self.vk_session.method('groups.getMembers', {
                'group_id': group_id,
                'fields': 'sex, city',
                'offset': 500000,
                'sort': 'id_desc'
            })['items'].__len__() > 900:
                return 50000 + random.randint(500, 5000)
            elif self.vk_session.method('groups.getMembers', {
                'group_id': group_id,
                'fields': 'sex, city',
                'offset': 100000,
                'sort': 'id_desc'
            })['items'].__len__() > 900:
                return 10000 + random.randint(100, 1000)
            elif self.vk_session.method('groups.getMembers', {
                'group_id': group_id,
                'fields': 'sex, city',
                'offset': 50000,
                'sort': 'id_desc'
            })['items'].__len__() > 900:
                return 5000 + random.randint(500, 5000)
            else:
                return 0

        group_id = search_parameters[1]
        number_of_result = search_parameters[2]
        offset = get_offset()
        members = [1, 2, 3]
        while members.__len__() > 0:
            try:
                members = self.vk_session.method('groups.getMembers', {
                    'group_id': group_id,
                    'fields': 'sex, city',
                    'offset': offset,
                    'sort': 'id_desc'
                })['items']
            except:
                time.sleep(1)
                offset += 1000

            self.do_search([member for member in members if member['sex'] == 1],
                           number_of_result)
            offset += 1000
        self.send_message('Поиск окончен, участники для проверки закончились')

    def search_message_handler(self):
        if not self.check_common_commands(self.selected_set):
            if self.message == 'команды':
                self.send_message(SEARCHING_COMMANDS_MESSAGE)
            elif self.message.__contains__('поиск по'):
                search_parameters = self.get_search_parameters()
                if search_parameters.__len__() != 3:
                    self.send_message('проверьте параметры поиска')
                    return
                self.send_message('параметры поиска: ' +
                                  ", ".join(search_parameters) +
                                  "; набор: " + self.selected_set)
                search_by = search_parameters[0]
                if search_by == 'городу':
                    try:
                        self.search_by_city(search_parameters[1], search_parameters[2])
                    except Exception as exc:
                        logger.error(exc)
                        self.send_message('Поиск прекращен')
                elif search_by == 'паблику':
                    try:
                        if self.search_by_group(search_parameters) == -1:
                            self.send_message('Поиск был прерван вами')
                    except Exception as exc:
                        logger.error(exc)
                        self.send_message('Поиск прекращен')
                else:
                    self.send_message('Возможен поиск только по'
                                      ' паблику или городу')
            elif self.message.__contains__('другой режим'):
                with open(os.path.join(os.path.dirname(sys.argv[0]),
                                       'settings_dir/selected_mode.txt'),
                          'w'):
                    pass
                with open(os.path.join(os.path.dirname(sys.argv[0]),
                                       'settings_dir/selected_mode.txt'),
                          'w') as mode_file:
                    mode_file.write('test')

                self.send_message('Выбран режим тестирования')
            else:
                self.send_message('Нет такой команды')
