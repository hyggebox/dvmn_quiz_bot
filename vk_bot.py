import logging
from random import choice
from time import sleep

import redis
from environs import Env
import vk_api as vk
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.utils import get_random_id
from vk_api.longpoll import VkLongPoll, VkEventType

from quiz_helpers import (get_questions,
                          NEW_QUESTION_TEXT,
                          GIVE_UP_TEXT,
                          GET_SCORE_TEXT)


logger = logging.getLogger('Logger')

SCORE_ID_PATTERN = 'score{}'
USER_ID_PATTERN = 'vk{}'


class VKLogsHandler(logging.Handler):

    def __init__(self, user_id, vk_api):
        super().__init__()
        self.user_id = user_id
        self.vk_api = vk_api

    def emit(self, record):
        log_entry = self.format(record)
        self.vk_api.messages.send(user_id=self.user_id,
                                  message=log_entry,
                                  random_id=get_random_id())


def create_keyboard():
    keyboard = VkKeyboard(one_time=True)

    keyboard.add_button(NEW_QUESTION_TEXT, color=VkKeyboardColor.PRIMARY)
    keyboard.add_button(GIVE_UP_TEXT, color=VkKeyboardColor.SECONDARY)
    keyboard.add_line()
    keyboard.add_button(GET_SCORE_TEXT, color=VkKeyboardColor.SECONDARY)
    keyboard.add_line()
    keyboard.add_button('Начать сначала', color=VkKeyboardColor.SECONDARY)
    return keyboard


def start_quiz(event, vk_api, redis_db):
    redis_db.set(SCORE_ID_PATTERN.format(event.user_id), 0)
    vk_api.messages.send(
        user_id=event.user_id,
        random_id=get_random_id(),
        keyboard=create_keyboard().get_keyboard(),
        message='Привет! Сыграем в викторину? Жми "Новый вопрос".'
    )


def send_new_question(event, vk_api, questions, redis_db):
    question_to_send = choice(list(questions))
    redis_db.set(USER_ID_PATTERN.format(event.user_id), question_to_send)

    vk_api.messages.send(
        user_id=event.user_id,
        random_id=get_random_id(),
        keyboard=create_keyboard().get_keyboard(),
        message=question_to_send
    )


def handle_solution_attempt(event, vk_api, questions, redis_db):
    user_answer = event.text
    question = redis_db.get(USER_ID_PATTERN.format(event.user_id))
    answer = questions[question]

    if user_answer.lower() == answer.lower():
        redis_db.incr(SCORE_ID_PATTERN.format(event.user_id))
        msg = '🔥 Поздравляю! Это правильный ответ!\nЕщё вопросик?'
    else:
        msg = f'😒 Неправильно… Попробуешь ещё раз?'

    vk_api.messages.send(
        user_id=event.user_id,
        random_id=get_random_id(),
        keyboard=create_keyboard().get_keyboard(),
        message=msg
    )


def send_answer(event, vk_api, questions, redis_db):
    question = redis_db.get(USER_ID_PATTERN.format(event.user_id))
    answer = questions[question]

    vk_api.messages.send(
        user_id=event.user_id,
        random_id=get_random_id(),
        keyboard=create_keyboard().get_keyboard(),
        message=f'Правильный ответ: {answer}'
    )
    send_new_question(event, vk_api, questions, redis_db)


def get_score(event, vk_api, redis_db):
    vk_api.messages.send(
        user_id=event.user_id,
        random_id=get_random_id(),
        keyboard=create_keyboard().get_keyboard(),
        message=f'Счёт: {redis_db.get(SCORE_ID_PATTERN.format(event.user_id))} баллов'
    )


def main():
    env = Env()
    env.read_env()

    db_endpoint = env.str('DB_ENDPOINT')
    db_port = env.int('DB_PORT')
    db_password = env.str('DB_PASSWORD')

    redis_db = redis.StrictRedis(host=db_endpoint, port=db_port,
                                 password=db_password, decode_responses=True)

    vk_session = vk.VkApi(token=env.str('VK_TOKEN'))
    vk_api = vk_session.get_api()
    longpoll = VkLongPoll(vk_session)

    logger.setLevel(level=logging.INFO)
    logger.addHandler(VKLogsHandler(env.str('VK_ADMIN_USER_ID'), vk_api))
    logger.info('Бот запущен')

    questions = get_questions()

    while True:
        try:
            for event in longpoll.listen():
                if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                    if event.text.lower() == 'начать сначала' or event.text.lower() == 'начать':
                        start_quiz(event, vk_api, redis_db)
                    elif event.text == NEW_QUESTION_TEXT:
                        send_new_question(event, vk_api, questions, redis_db)
                    elif event.text == GIVE_UP_TEXT:
                        send_answer(event, vk_api, questions, redis_db)
                    elif event.text == GET_SCORE_TEXT:
                        get_score(event, vk_api, redis_db)
                    else:
                        handle_solution_attempt(event, vk_api, questions, redis_db)
        except Exception as err:
            logger.exception(f"⚠ Ошибка бота:\n\n {err}")
            sleep(60)


if __name__ == '__main__':
    main()
