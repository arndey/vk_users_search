import sys

import os

WHORE_PHRASES = ['жду звонка', 'интим', 'с подружкой']

with open(os.path.join(os.path.dirname(sys.argv[0]),
                       'help_messages/common_part.txt'),
          'r', encoding='utf-8') as txt:
    COMMON_HELP_MESSAGE_PART = txt.read() + '\n\n'

with open(os.path.join(os.path.dirname(sys.argv[0]),
                       'help_messages/search_message.txt'),
          'r', encoding='utf-8') as txt:
    SEARCHING_COMMANDS_MESSAGE = COMMON_HELP_MESSAGE_PART + txt.read()

with open(os.path.join(os.path.dirname(sys.argv[0]),
                       'help_messages/test_message.txt'),
          'r', encoding='utf-8') as txt:
    TESTING_COMMANDS_MESSAGE = COMMON_HELP_MESSAGE_PART + txt.read()