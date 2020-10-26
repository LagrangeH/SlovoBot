# !/usr/bin/env python3
from bot_head import BotUtils, SetUnicVariables, DataBase
from bot_head import longpoll, users
import traceback
from vk_api.bot_longpoll import VkBotEventType
from loguru import logger


@logger.catch()
def run():
    for event in longpoll.listen():
        try:
            if event.type == VkBotEventType.MESSAGE_NEW and event.from_user:
                response = event.object.message['text'].lower()
                peer_id = event.object.message['peer_id']
                user_id = event.object.from_id
                db = DataBase
                bot = BotUtils(event, response, user_id, peer_id)
                kb = bot.create_keyboard()
                users[user_id] = SetUnicVariables() if users.get(user_id) is None else users[user_id]
                if response == '123':
                    bot.send_message('Нажми кнопку, чтобы начать', kb)
                if response is not None:
                    bot.send_message('Info', kb)
        except:
            logger.error(traceback.format_exc())


if __name__ == '__main__':
    logger.info("Bot launched")
    run()
