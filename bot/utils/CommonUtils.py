import os
from glob import glob

import dlib
import sys

import shutil

import requests
import time
import vk_api
from skimage import io
from scipy.spatial import distance

from beauty_neural_correct.settings import SETS_PATH_PREFIX


class CommonUtils:
    def __init__(self, vk_session, suter_user_id, message, item):
        self.vk_session = vk_session
        self.suter_user_id = suter_user_id
        self.message = message
        self.item = item

    def send_message(self, message_to_send='', attachment=''):
        self.vk_session.method('messages.send', {
            'user_id': self.suter_user_id,
            'message': message_to_send,
            'attachment': attachment
        })

    def get_io_images(self, set_path):
        return [[image, io.imread(set_path + '/' + image)]
                for image in os.listdir(set_path)]

    def get_beauty_score(self, img1, img2):
        sp = dlib.shape_predictor(
            'data_for_neural/shape_predictor_68_face_landmarks.dat')
        facerec = dlib.face_recognition_model_v1(
            'data_for_neural/dlib_face_recognition_resnet_model_v1.dat')
        detector = dlib.get_frontal_face_detector()

        first_dets = detector(img1, 1)
        for k, d in enumerate(first_dets):
            shape1 = sp(img1, d)
        face_descriptor1 = facerec.compute_face_descriptor(img1, shape1)

        second_dets = detector(img2, 1)
        for k, d in enumerate(second_dets):
            shape2 = sp(img2, d)
        face_descriptor2 = facerec.compute_face_descriptor(img2, shape2)

        return distance.euclidean(face_descriptor1, face_descriptor2)

    def get_set_name(self, prefix):
        return self.message[prefix.__len__():].strip()

    def get_message_for_set(self):
        sets = glob(SETS_PATH_PREFIX + '*')
        return "\n".join(
            [
                set[SETS_PATH_PREFIX.__len__():].strip().split('\\').pop() + ': ' +
                str(os.listdir(set).__len__()) for set in sets
            ]
        )

    def create_set(self):
        set_name = self.get_set_name(prefix='создать')
        if set_name == '' or set_name is None:
            self.send_message('Введите название набора')
            return
        os.mkdir(SETS_PATH_PREFIX + set_name)

        return set_name

    def choose_set(self):
        set_name = self.get_set_name(prefix='выбрать')
        if not os.path.exists(SETS_PATH_PREFIX + set_name):
            self.send_message('Не существует такого набора')
            return
        selected_set = set_name

        with open(os.path.join(os.path.dirname(sys.argv[0]),
                               'settings_dir/selected_set.txt'), 'w'):
            pass
        with open(os.path.join(os.path.dirname(sys.argv[0]),
                               'settings_dir/selected_set.txt'),
                  'w') as set_txt:
            set_txt.write(selected_set)
        self.send_message('Выбран ' + selected_set)

    def add_in_set(self, get_current_photo_index):
        set_name = self.get_set_name(prefix='Добавить в')
        set_path = SETS_PATH_PREFIX + set_name
        if not os.path.exists(set_path):
            self.send_message('Не существует такого набора')
            return None, None
        try:
            attachments = self.item['attachments']
        except:
            self.send_message('Не вижу фотографий')
            return None, None

        for att in attachments:
            if att['type'] == 'photo':
                index = get_current_photo_index(set_path)
                bytes = requests.get(att['photo']['photo_604']).content
                with open(set_path + '/' + str(index) + '.jpg', 'wb') as new:
                    new.write(bytes)
                index += 1
            else:
                self.send_message('Мне нужны только фотографии')
                return None, None

        return set_name, attachments

    def get_current_photo_index(self, set_path):
        index = -1
        for photo in os.listdir(set_path):
            photo_index = int(photo.split('.')[0])
            if photo_index > index:
                index = photo_index

        return index + 1

    def send_photos(self, set_path):
        for name in os.listdir(set_path):
            upload = vk_api.VkUpload(self.vk_session)
            photo_data = upload.photo_messages(set_path + '/' + name)

            self.send_message(name.split('.')[0],
                              attachment='photo{owner_id}_{media_id}'
                              .format(owner_id=int(photo_data[0]['owner_id']),
                                      media_id=photo_data[0]['id']))
            time.sleep(0.5)

    def remove_photos(self, set_path, str_with_numbers):
        removed_counter = 0
        nums = [int(num) for num in str_with_numbers.strip().split(',')]
        for photo in os.listdir(set_path):
            if nums.__contains__(int(photo.split('.')[0])):
                os.remove(set_path + '/' + photo)
                removed_counter += 1

        return removed_counter == nums.__len__()

    def check_common_commands(self, selected_set):
        with open(os.path.join(os.path.dirname(sys.argv[0]),
                               'settings_dir/difference.txt'),
                  'r') as difference_txt:
            minimum_difference = float(difference_txt.read())

        if self.message == 'наборы':
            self.send_message(self.get_message_for_set())
        elif self.message.__contains__('создать'):
            set_name = self.create_set()
            self.send_message('Создан набор ' + set_name)
        elif self.message.__contains__('добавить в'):
            set_name, attachments = self.add_in_set(self.get_current_photo_index)
            if set_name is not None:
                self.send_message('В {set} добавлено {num} фотографий'
                                  .format(set=set_name, num=attachments.__len__()))
        elif self.message.__contains__('удалить') and \
                not self.message.__contains__('удалить в'):
            set_name = self.get_set_name(prefix='удалить')
            if not os.path.exists(SETS_PATH_PREFIX + set_name):
                self.send_message('Не существует такого набора')
                return True

            shutil.rmtree(SETS_PATH_PREFIX + set_name)
            self.send_message('Удален набор ' + set_name)
        elif self.message.__contains__('просмотреть из'):
            set_name = self.get_set_name(prefix='просмотреть из')
            if not os.path.exists(SETS_PATH_PREFIX + set_name):
                self.send_message('Не существует такого набора')
                return True

            self.send_photos(SETS_PATH_PREFIX + set_name)
        elif self.message.__contains__('удалить в'):
            set_name = self.message['удалить в'.__len__():self.message.find(':')].strip()
            if not os.path.exists(SETS_PATH_PREFIX + set_name):
                self.send_message('Не существует такого набора')
                return True

            try:
                if not self.remove_photos(SETS_PATH_PREFIX + set_name, self.message.split(':')[1]):
                    self.send_message('Указан минимум 1 несуществующий номер.'
                                                      ' Существующие были удалены')
                else:
                    self.send_message('Удалено')
            except:
                self.send_message('Правильно ли введены номера фотографий?')
        elif self.message.__contains__('выбрать'):
            self.choose_set()
        elif self.message.__contains__('текущий набор'):
            self.send_message('Выбран ' + selected_set)
        elif self.message.__contains__('текущая жесткость'):
            self.send_message(str(minimum_difference))
        elif self.message.__contains__('установить жесткость'):
            fixed_difference = self.message['установить жесткость'.__len__():].strip()
            try:
                minimum_difference = float(fixed_difference)
            except:
                self.send_message('введите корректное число')
                return True

            with open(os.path.join(os.path.dirname(sys.argv[0]),
                                   'settings_dir/difference.txt'), 'w'):
                pass
            with open(os.path.join(os.path.dirname(sys.argv[0]),
                                   'settings_dir/difference.txt'),
                      'w') as difference_txt:
                difference_txt.write(str(fixed_difference))
            self.send_message('установлена жесткость: ' +
                                              str(minimum_difference))
        else:
            return False

        return True
