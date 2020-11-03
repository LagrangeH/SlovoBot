# !/usr/bin/env python3
# -*- coding: utf-8 -*-
import threading
import time
import traceback
import json

import messages

from random import randrange
from datetime import datetime
from loguru import logger
from vk_api.bot_longpoll import VkBotEventType
from vk_api.utils import get_random_id

from bot_head import BotUtils, SetUniqueVariables, DataBase
from bot_head import long_poll, users, clocks, used_words, vk, vk_session, keyboard_for_word
from bot_head import word_count_without_bug


@logger.catch()
def run():
    logger.info('LongPoll Thread started')
    for event in long_poll.listen():
        try:
            if event.type == VkBotEventType.MESSAGE_NEW and event.from_user:

                db = DataBase()  # Подключение к базе данных
                response = event.obj.text.lower() if len(event.obj.text) > 0 else ' '   # Ответ пользователя
                payload = event.obj.payload     # По какой-то причине словарь превращается в строку
                peer_id, user_id = event.obj.peer_id, event.obj.from_id
                bot = BotUtils(event, response, user_id, peer_id, users)
                kb = bot.create_keyboard()
                inline_kb = bot.create_inline_kb(payload)
                # Словарь, где ключ - id юзера, значение - экземпляр класса
                users[user_id] = SetUniqueVariables() if users.get(user_id) is None else users[user_id]

                if not payload:
                    if response[:5] == 'найти':
                        word = response[6:]
                        if db.check_word(word):
                            word_data = db.data_by_word(word)
                            msg = word_data[1].upper() + ' - это\n' + word_data[2]
                            bot.send_message(msg, keyboard_for_word(word_data[1]))
                        else:
                            bot.send_message('Этого слова нет в моём словаре', kb)
                    elif response[0] == '#':  # Отправить "карточку" слова из словаря юзера по номеру в нём
                        try:
                            word = users[user_id].user_diction[int(response[1:]) - 1].capitalize()
                            word += ' - это\n' + db.data_by_word(word)[2]
                            bot.send_message(word, kb)
                        except IndexError:
                            bot.send_message('Это число превышает количество слов в твоем словаре!', kb)
                        except ValueError:
                            bot.send_message('Нужно ввести число!', kb)

                elif 'info' in payload:
                    bot.send_message(messages.info, kb)
                elif 'menu' in payload:
                    bot.send_message('Меню', kb)
                elif 'settings' in payload:
                    bot.send_message('Настройки', kb)
                elif "user_dict" in payload:
                    if not users[user_id].user_diction:
                        bot.send_message('Ты не добавил понравившихся слов', kb)
                    else:
                        msg = 'Понравившиеся слова:\n'
                        for i in range(len(users[user_id].user_diction)):
                            msg += f'{i+1}. {users[user_id].user_diction[i]}\n'
                        bot.send_message(msg, kb)
                elif 'clear_diction' in payload:
                    bot.send_message('Твой словарь будет полностью очищен. Ты подтверждаешь?', inline_kb)
                elif 'cleared' in payload:
                    users[user_id].clear_diction()
                    bot.send_message('Твой словарь очищен', kb)

                else:
                    if "not_supported_button" in payload:
                        if "добавлено" in payload:
                            word = payload[116:-31]
                            try:
                                add_word = users[user_id].add_to_diction(word)
                            except RuntimeError:
                                bot.send_message('Это слово уже в твоём словаре', kb)
                            else:
                                bot.send_message(f"Слово «{word.lower()}» добавлено в твой словарь", kb)
                        elif "удалено" in payload:
                            word = payload[116:-32]
                            try:
                                del_word = users[user_id].del_from_diction(word)
                            except RuntimeError:
                                bot.send_message('Этого слова не было в твоём словаре', kb)
                            else:
                                bot.send_message(f"Слово «{word.lower()}» удалено из твоего словаря", kb)
                    else:
                        bot.send_message('Я тебя не понимаю😟', kb)

            elif event.type == VkBotEventType.MESSAGE_EVENT:
                if event.object.payload.get('type') == 'show_snackbar':
                    payload = event.object.payload
                    user_id = event.obj.user_id

                    if 'добавлено' in payload['text']:  # Если добавить слово в словарь юзера
                        word = payload['text'][7:-26]
                        try:
                            add_word = users[user_id].add_to_diction(word)
                        except RuntimeError:
                            payload['text'] = 'Это слово уже в твоём словаре'

                    elif 'удалено' in payload['text']:  # Если удалить слово из словаря юзера
                        word = payload['text'][7:-27]
                        try:
                            del_word = users[user_id].del_from_diction(word)
                        except RuntimeError:
                            payload['text'] = 'Этого слова не было в твоём словаре'

                    vk_session.messages.sendMessageEventAnswer(
                        event_id=event.object.event_id,
                        user_id=event.object.user_id,
                        peer_id=event.object.peer_id,
                        event_data=json.dumps(payload))

        except:
            logger.error(traceback.format_exc())


@logger.catch()
def timer():
    logger.info('Timer Thread started')
    while True:
        try:
            db = DataBase()
            for user in users.keys():  # Итерируем имеющиеся id юзеров
                if users[user].get_timer()['timer_status'] is True:  # Проверяем тех юзеров, у которых включен таймер
                    # Создаем словарь, в котором ключём является время таймера, а значением - массив с id пользователей
                    clocks[users[user].get_timer()['timer']] = []
                    clocks[users[user].get_timer()['timer']].append(user)

            # Если боту еще никто не писал
            if clocks == {}:
                time.sleep(3)
                continue

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

            if (today.month + today.day / 100) not in used_words:
                word_data = db.data_by_id(randrange(0, stop=word_count_without_bug()))
                word_id, word, word_interpretation, first_letter = word_data
                used_words[today.month + today.day / 100] = word_id
            else:
                word_data = db.data_by_id(used_words[today.month + today.day / 100])
                word_id, word, word_interpretation, first_letter = word_data
                used_words[today.month + today.day / 100] = word_id

            message = word.upper() + ' - это\n' + word_interpretation

            time.sleep(delta_time)  # Ждём таймер TODO: поставить после дебага здесь

            for user in clocks[time_for_timer]:
                vk.method('messages.send',
                          {'peer_id': user, 'user_id': user,
                           'message': message, 'random_id': get_random_id(),
                           'attachment': None, 'keyboard': keyboard_for_word(word)})
            else:
                logger.info('Рассылка отправлена')

            # time.sleep(delta_time)  # Ждём таймер TODO: убрать после дебага
        except:
            logger.error(traceback.format_exc())


if __name__ == '__main__':
    threading.Thread(target=run, name='LongPollThread').start()
    threading.Thread(target=timer, name='TimerThread').start()
