# !/usr/bin/env python3
from bot_head import BotUtils, SetUnicVariables, DataBase
from bot_head import longpoll, users
import traceback
from vk_api.bot_longpoll import VkBotEventType
from loguru import logger
import threading
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
                db = DataBase
                bot = BotUtils(event, response, user_id, peer_id)
                kb = bot.create_keyboard()
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
            for user in users.keys():
                if users[user].get_timer()['timer_status'] is True:
                    print(True)
                else:
                    print(False)
            time.sleep(3)
        except:
            logger.error(traceback.format_exc())


if __name__ == '__main__':
    threading.Thread(target=run, name='LongPollThread').start()
    threading.Thread(target=timer, name='TimerThread').start()
