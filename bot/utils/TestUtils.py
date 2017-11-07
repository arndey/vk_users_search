import os
import requests
import sys

from skimage import io

from beauty_neural_correct.settings import SETS_PATH_PREFIX, logger
from bot.messages_and_phrases import TESTING_COMMANDS_MESSAGE
from bot.utils.CommonUtils import CommonUtils


class TestUtils(CommonUtils):
    def __init__(self, message, suter_user_id, item, vk_session, selected_set):
        super().__init__(vk_session, suter_user_id, message, item)
        self.suter_user_id = suter_user_id
        self.item = item
        self.vk_session = vk_session
        self.selected_set = selected_set

    def test(self):
        with open(os.path.join(os.path.dirname(sys.argv[0]),
                               'settings_dir/difference.txt'),
                  'r') as difference_txt:
            minimum_difference = float(difference_txt.read())
        try:
            attachments = self.item['attachments']
        except:
            self.send_message('жду фото')
            return

        if attachments.__len__() != 1:
            self.send_message('жду только 1 фото')
            return
        if self.item['attachments'][0]['type'] == 'photo':
            bytes = requests.get(attachments[0]['photo']['photo_604']).content
            with open('current_girl.jpg', 'wb') as new:
                new.write(bytes)
        else:
            self.send_message('жду фото')

        images = self.get_io_images(SETS_PATH_PREFIX + self.selected_set)
        for image in images:
            try:
                current_score = self.get_beauty_score(image[1],
                                                      io.imread('current_girl.jpg'))
            except Exception as exc:
                logger.error(str(exc) + ' -> ' + image[0])
                exc_message = ['Что-то с тестируемой фотографией не так'
                               if str(exc).__eq__('local variable \'shape2\' '
                                                  'referenced before assignment')
                               else 'Что-то с фотографией {photo} '
                                    'из набора не так'.format(photo=image[0])]
                self.send_message(exc_message[0])
                break

            if current_score < minimum_difference:
                self.send_message('👍')
                break
        else:
            self.send_message('👎')

    def testing_message_handler(self):
        if not self.check_common_commands(self.selected_set):
            if self.message == 'команды':
                self.send_message(TESTING_COMMANDS_MESSAGE)
            elif self.message.__contains__('тест'):
                self.test()
            elif self.message.__contains__('другой режим'):
                with open(os.path.join(os.path.dirname(sys.argv[0]),
                                       'settings_dir/selected_mode.txt'),
                          'w'):
                    pass
                with open(os.path.join(os.path.dirname(sys.argv[0]),
                                       'settings_dir/selected_mode.txt'),
                          'w') as mode_file:
                    mode_file.write('search')

                self.send_message('Выбран режим поиска')
            else:
                self.send_message('Нет такой команды в режиме тестирования')
