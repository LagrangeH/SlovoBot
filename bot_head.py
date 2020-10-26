import traceback
from data import TOKEN
import vk_api
from vk_api.bot_longpoll import VkBotLongPoll
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.utils import get_random_id
from loguru import logger
import sqlite3

# Авторизация ВК
vk = vk_api.VkApi(token=TOKEN)
vk.get_api()
longpoll = VkBotLongPoll(vk, 194597333)
users = {}  # Словарь id всех пользователей со значением уникального класса
logger.add("errors.log", format="{time} {level} {message}", level="ERROR", rotation="20 KB", compression="zip")


class BotUtils:
    def __init__(self, event, response, user_id, peer_id):
        self.event = event
        self.response = response
        self.user_id = user_id
        self.peer_id = peer_id

    def edit_message(self, message, message_id):
        return vk.method('messages.edit',
                         {'peer_id': self.peer_id,
                          'message': message,
                          'message_id': message_id})

    def send_message(self, message, kb, attachment=None):
        return vk.method('messages.send',
                         {'peer_id': self.peer_id, 'user_id': self.user_id,
                          'message': message, 'random_id': get_random_id(),
                          'attachment': attachment, 'keyboard': kb})

    def create_inline_kb(self):
        pass
        # kb = VkKeyboard(inline=True)

    def create_keyboard(self):
        kb = VkKeyboard(one_time=False)
        if self.response is not None:
            kb.add_button('1', color=VkKeyboardColor.SECONDARY)
            kb.add_button('2', color=VkKeyboardColor.SECONDARY)
        else:
            kb.add_button('Начать', color=VkKeyboardColor.SECONDARY)
        kb = kb.get_keyboard()
        return kb


class SetUnicVariables:
    def __init__(self):
        self.user_diction = {}
        self.user_timer = {'timer': '09:00', 'timer_status': True}

    def get_timer(self):
        return self.user_timer

    def add_to_dicton(self, word):
        pass

    def change_timer(self):
        pass

    def off_timer(self):
        self.user_timer['timer_status'] = False
        return 'Timer for user disabled'

    def on_timer(self):
        self.user_timer['timer_status'] = True
        return 'Timer for user enabled'


class DataBase:
    def __init__(self):
        self.conn = sqlite3.connect('dictionary.db')
        self.cur = self.conn.cursor()
        self.cur.execute("""CREATE TABLE IF NOT EXISTS words(
            id INT,
            word TEXT PRIMARY KEY,
            interpretation TEXT,
            first_letter TEXT);""")
        self.conn.commit()

    def _commit(function):
        def f(self):
            function(self)
            self.conn.commit()
        return f

    @_commit
    def add(self, word: str, interpretation: str):
        self.cur.execute("SELECT id FROM words")
        leng = len(self.cur.fetchall())
        self.conn.commit()
        try:
            self.cur.execute("INSERT INTO words(id, word, interpretation, first_letter)"
                             "VALUES({}, '{}', '{}', '{}');".format(leng, word, interpretation, word[0]))
            return "Success"
        except:
            logger.error(traceback.format_exc())

        # TODO: Сделать туть выше по-другому (без .format())

    @_commit
    def data_by_word(self, word: str):
        self.cur.execute("SELECT * FROM words WHERE word='{}';".format(word))
        return self.cur.fetchone()

    @_commit
    def data_by_id(self, id: int):
        self.cur.execute("SELECT * FROM words WHERE id='{}';".format(id))
        return self.cur.fetchone()

    @_commit
    def check_word(self, word: str):
        self.cur.execute("SELECT word FROM words WHERE word='{}';".format(word))
        if self.cur.fetchone() is None:
            return False
        else:
            return True
