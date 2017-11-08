# vk_users_search
Поиск пользователей vk.com, похожих на людей из выбранного наобора фотографий в виде бота.
Чтобы узнать как создать свой набор и другие функции, напишите ему "команды".
В режиме тестирования и поиска команды отличаются. <br><br>
[Примеры наборов фотографий](bot/landmark_sets/)

INSTALLATION
------------
Смотреть описание в [requirements.txt](requirements.txt)

START
-----
В [settings](beauty_neural_correct/settings.py) заполните TOKEN сообщества,
а также заполните [файл с логином и паролем](bot/settings_dir/loginpassword.txt) от страницы пользователя. 
Это необходимо, так как не все методы vk API доступны с ключом сообщества. <br><br> 
Для запуска из корня проекта введите команду `python bot\bot_vk.py`
