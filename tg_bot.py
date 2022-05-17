import logging
from enum import Enum, auto
from functools import partial
from random import choice
from time import sleep

import redis
from environs import Env
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (CommandHandler,
                          MessageHandler,
                          Filters,
                          CallbackContext,
                          Updater,
                          ConversationHandler)

from quiz_helpers import (get_questions,
                          NEW_QUESTION_TEXT,
                          GIVE_UP_TEXT,
                          GET_SCORE_TEXT)


SCORE_ID_PATTERN = 'tg_score{}'


logger = logging.getLogger('TGBotLogger')


class State(Enum):
    CHOOSE = auto()
    ENTER_ANSWER = auto()


def get_answer(user_id, context):
    question = context.bot_data['redis'].get(user_id)
    return context.bot_data['questions'][question]


def start(update: Update, context: CallbackContext, redis_db):
    redis_db.set(SCORE_ID_PATTERN.format(update.effective_user.id), 0)

    reply_keyboard = [
        [NEW_QUESTION_TEXT, GIVE_UP_TEXT],
        [GET_SCORE_TEXT]
    ]
    reply_markup = ReplyKeyboardMarkup(reply_keyboard)

    user = update.effective_user
    update.message.reply_markdown_v2(
        text=f'Привет, {user.mention_markdown_v2()}\nДавай поиграем в викторину\!',
        reply_markup=reply_markup
    )
    return State.CHOOSE


def send_new_question(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    question_to_send = choice(list(context.bot_data['questions']))
    context.bot_data['redis'].set(user_id, question_to_send)

    update.message.reply_text(text=question_to_send)

    return State.ENTER_ANSWER


def handle_solution_attempt(update: Update, context: CallbackContext, redis_db):
    user_answer = update.message.text
    answer = get_answer(update.effective_user.id, context)

    if user_answer.lower() == answer.lower():
        redis_db.incr(SCORE_ID_PATTERN.format(update.effective_user.id))
        msg = '🔥 Поздравляю! Это правильный ответ!\nЕщё вопросик?'
        update.message.reply_text(text=msg)
        return State.CHOOSE

    msg = f'😒 Неправильно… Попробуешь ещё раз?'
    update.message.reply_text(text=msg)
    return State.ENTER_ANSWER


def send_answer(update: Update, context: CallbackContext):
    answer = get_answer(update.effective_user.id, context)
    update.message.reply_text(text=f'Правильный ответ: {answer}')
    send_new_question(update, context)


def get_score(update: Update, context: CallbackContext, redis_db):
    score = redis_db.get(SCORE_ID_PATTERN.format(update.effective_user.id))
    update.message.reply_text(f'Счёт {score}')
    return State.CHOOSE


def end_quiz(update: Update, context: CallbackContext, redis_db):
    score = redis_db.get(SCORE_ID_PATTERN.format(update.effective_user.id))
    update.message.reply_text(
        f'Спасибо за игру! Финальный счёт {score}'
    )
    return ConversationHandler.END


def main():
    env = Env()
    env.read_env()

    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO)

    tg_bot_token = env.str('TG_BOT_TOKEN')
    db_endpoint = env.str('DB_ENDPOINT')
    db_port = env.int('DB_PORT')
    db_password = env.str('DB_PASSWORD')

    redis_db = redis.StrictRedis(host=db_endpoint, port=db_port,
                                 password=db_password, decode_responses=True)

    updater = Updater(tg_bot_token)
    dispatcher = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler('start', partial(start, redis_db=redis_db))
        ],

        states={
            State.CHOOSE: [
                MessageHandler(
                    Filters.text(NEW_QUESTION_TEXT),
                    send_new_question
                ),
                MessageHandler(
                    Filters.text(GET_SCORE_TEXT),
                    get_score
                ),
            ],

            State.ENTER_ANSWER: [
                MessageHandler(
                    Filters.text(GIVE_UP_TEXT),
                    send_answer
                ),
                MessageHandler(
                    Filters.text(GET_SCORE_TEXT),
                    partial(get_score, redis_db=redis_db)
                ),
                MessageHandler(
                    Filters.text & ~Filters.command,
                    partial(handle_solution_attempt, redis_db=redis_db)
                ),
            ],
        },

        fallbacks=[
            CommandHandler(
                'finish',
                partial(end_quiz, redis_db=redis_db)
            )
        ]
    )

    dispatcher.bot_data['questions'] = get_questions()
    dispatcher.bot_data['redis'] = redis_db
    dispatcher.add_handler(conv_handler)

    while True:
        try:
            updater.start_polling()
            updater.idle()
        except Exception as err:
            logger.exception(f"⚠ Ошибка бота:\n\n {err}")
            sleep(60)


if __name__ == '__main__':
    main()
