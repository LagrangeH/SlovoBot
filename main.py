# !/usr/bin/env python3
from bot_head import BotUtils, SetUnicVariables, DataBase
from bot_head import longpoll, users, clocks
import traceback
from vk_api.bot_longpoll import VkBotEventType
from loguru import logger
import threading
from datetime import datetime
import time


@logger.catch()
def run():
    logger.info('LongPoll Thread started')
    for event in longpoll.listen():
        try:
            if event.type == VkBotEventType.MESSAGE_NEW and event.from_user:
                response = event.obj.text.lower()
                peer_id = event.obj.peer_id
                user_id = event.obj.from_id
                db = DataBase()
                bot = BotUtils(event, response, user_id, peer_id)
                kb = bot.create_keyboard()  # Клавиатура
                # Словарь, где ключ - id юзера, значение - экземпляр класса
                users[user_id] = SetUnicVariables() if users.get(user_id) is None else users[user_id]
                if response == '123':
                    bot.send_message('Нажми кнопку, чтобы начать', kb)
                else:
                    bot.send_message('Я тебя не понимаю(', kb)
        except:
            logger.error(traceback.format_exc())


@logger.catch()
def timer():
    logger.info('Timer Thread started')
    while True:
        try:
            for user in users.keys():  # Итерируем имеющиеся id юзеров
                if users[user].get_timer()['timer_status'] is True:  # Проверяем тех юзеров, у которых включен таймер
                    # Создаем словарь, в котором ключём является время таймера, а значением - массив с id пользователей
                    clocks[users[user].get_timer()['timer']] = user

            # Создаем массив разновидностей времен таймера
            cl = []
            for key in clocks.keys():  # Создадим неупорядоченный массив
                cl.append(key)
            clocks_array = []
            for i in set(cl):  # Упорядочим массив по возрастанию
                clocks_array.append(i)

            today = datetime.now()
            current_time = today.hour + today.minute / 100  # Текущее время в формате hh.mm (тип - float)

            # Находим ближайший таймер
            for t in clocks_array:
                if current_time <= t:  # Если ближайший таймер сегодня
                    time_for_timer = t
                    day = 0  # Сегодня
                    break  # Массив упорядочен по возрастанию: дальнейшая проверка не требуется
            else:  # Если ближайший таймер завтра
                time_for_timer = clocks_array[0]  # Нужен первый элемент, т.к. массив упорядочен по возрастанию
                day = 1  # Завтра

            # Определяем время таймера
            if today.day < 30:
                alarm_time = datetime(today.year, today.month, today.day + 1,
                                      int(time_for_timer), int('{:.0f}'.format(time_for_timer % 1 * 100)))
            else:  # Новый месяц
                if (today.month in [1, 3, 5, 7, 8, 10] and today.day == 31) or today.month in [2, 4, 6, 9, 11]:
                    alarm_time = datetime(today.year, today.month + 1, 1,
                                          int(time_for_timer), int('{:.0f}'.format(time_for_timer % 1 * 100)))
                else:  # НОВЫЙ ГОООД
                    alarm_time = datetime(today.year + 1, 1, 1,
                                          int(time_for_timer), int('{:.0f}'.format(time_for_timer % 1 * 100)))

            delta_time = (alarm_time - today).total_seconds() // 1
            time.sleep(delta_time)  # Ждём таймер
        except:
            logger.error(traceback.format_exc())


if __name__ == '__main__':
    threading.Thread(target=run, name='LongPollThread').start()
    threading.Thread(target=timer, name='TimerThread').start()
