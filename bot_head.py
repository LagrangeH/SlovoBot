# !/usr/bin/env python3
# -*- coding: utf-8 -*-
import sqlite3
import traceback

import vk_api
from loguru import logger
from vk_api.bot_longpoll import VkBotLongPoll
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.utils import get_random_id

from data import TOKEN

# Авторизация ВК
vk = vk_api.VkApi(token=TOKEN)
vk_session = vk.get_api()

long_poll = VkBotLongPoll(vk, 194597333)
users = {}  # Словарь id всех пользователей со значением уникального класса
logger.add("debug.log", format="{time} {level} {message}", level="DEBUG", rotation="100 KB", compression="zip")
clocks = {}  # Создаем словарь, в котором ключём является время таймера, а значением - массив с id пользователей
used_words = {}  # Словарь использованых слов в виде: data:id


def word_count_without_bug():
    conn = sqlite3.connect('dictionary.db')
    cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS words(
                id INT,
                word TEXT PRIMARY KEY,
                interpretation TEXT,
                first_letter TEXT);""")
    conn.commit()
    cur.execute("SELECT COUNT(id) FROM words;")
    leng = int(cur.fetchone()[0])
    return leng


def keyboard_for_word(word):
    kb = VkKeyboard(inline=True)
    kb.add_callback_button(label='Добавить', color=VkKeyboardColor.POSITIVE,
                           payload={"type": "show_snackbar",
                                    "text": f"Слово «{word.lower()}» добавлено в твой словарь"})
    kb.add_callback_button(label='Удалить', color=VkKeyboardColor.NEGATIVE,
                           payload={"type": "show_snackbar",
                                    "text": f"Слово «{word.lower()}» удалено из твоего словаря"})
    return kb.get_keyboard()


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

    # def __del__(self):
    #     # logger.info('Соединение с БД разорвано')
    #     self.conn.close()

    def word_count(self):
        self.cur.execute("SELECT COUNT(id) FROM words;")
        leng = int(self.cur.fetchone()[0])
        if leng is not None:
            return leng
        else:
            raise Exception('Словарь пустой')

    def add(self, word: str, interpretation: str):
        self.cur.execute("SELECT COUNT(id) FROM words;")
        leng = int(self.cur.fetchone()[0])
        try:
            self.cur.execute("INSERT INTO words VALUES(?, ?, ?, ?);", (leng, word, interpretation, word[0]))
            self.conn.commit()
            return "Success"
        except:
            logger.error(traceback.format_exc())

    def data_by_word(self, word):
        self.cur.execute("SELECT * FROM words WHERE word='{}';".format(word.capitalize()))
        return self.cur.fetchone()

    def data_by_id(self, id_):
        self.cur.execute("SELECT * FROM words WHERE id='{}';".format(id_))
        return self.cur.fetchone()

    def check_word(self, word):
        self.cur.execute("SELECT * FROM words WHERE word='{}';".format(word.capitalize()))
        fetch = self.cur.fetchall()
        if not fetch:
            return False
        else:
            return True


class SetUniqueVariables:
    def __init__(self):
        self.user_diction = []
        self.user_timer = {'timer': 9.0, 'timer_status': True}

    def get_timer(self):
        return self.user_timer

    def change_timer(self):
        pass

    def off_timer(self):
        self.user_timer['timer_status'] = False
        return 'Timer for user disabled'

    def on_timer(self):
        self.user_timer['timer_status'] = True
        return 'Timer for user enabled'

    def add_to_diction(self, word):
        if word not in self.user_diction:
            self.user_diction.append(word)
        else:
            raise RuntimeError

    def del_from_diction(self, word):
        try:
            self.user_diction.remove(word)
        except ValueError:
            raise RuntimeError

    def clear_diction(self):
        self.user_diction.clear()
        return True


class BotUtils:
    def __init__(self, event, response, user_id, peer_id, users_):
        self.event = event
        self.response = response
        self.user_id = user_id
        self.peer_id = peer_id
        self.users = users_
        self.users[self.user_id] = SetUniqueVariables() if users_.get(self.user_id) is None else users_[self.user_id]

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

    def create_inline_kb(self, payload):
        kb = VkKeyboard(inline=True)
        if 'clear_diction' in payload:
            kb.add_button('Подтверждаю', color=VkKeyboardColor.POSITIVE, payload=['cleared'])
        return kb.get_keyboard()

    def create_keyboard(self, *args):
        kb = VkKeyboard(one_time=False)
        if self.response == 'настройки':
            kb.add_button('Инфо', color=VkKeyboardColor.PRIMARY, payload=['info'])
            kb.add_button('Очистить мой словарь', color=VkKeyboardColor.NEGATIVE, payload=['clear_diction'])
            kb.add_line()
            kb.add_button('Меню', color=VkKeyboardColor.SECONDARY, payload=['menu', args])
        else:
            kb.add_button('Мой словарь', color=VkKeyboardColor.PRIMARY, payload=['user_dict'])
            kb.add_button('Настройки', color=VkKeyboardColor.SECONDARY, payload=['settings'])
        return kb.get_keyboard()
