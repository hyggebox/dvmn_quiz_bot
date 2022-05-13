import logging
from enum import Enum, auto
from functools import partial
from random import choice
from time import sleep

from environs import Env
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (CommandHandler,
                          MessageHandler,
                          Filters,
                          CallbackContext,
                          Updater,
                          ConversationHandler)

from quiz_helpers import (get_questions,
                          setup_redis_db,
                          NEW_QUESTION_TEXT,
                          GIVE_UP_TEXT,
                          GET_SCORE_TEXT)


logger = logging.getLogger('TGBotLogger')


class State(Enum):
    CHOOSE = auto()
    ENTER_ANSWER = auto()


def get_answer(user_id, context):
    question = context.user_data['redis'].get(user_id)
    return context.user_data['questions'][question]


def start(update: Update, context: CallbackContext, redis_db):
    context.user_data['questions'] = get_questions()
    context.user_data['redis'] = redis_db
    context.user_data['score'] = 0

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
    question_to_send = choice(list(context.user_data['questions']))
    context.user_data['redis'].set(user_id, question_to_send)

    update.message.reply_text(text=question_to_send)

    return State.ENTER_ANSWER


def handle_solution_attempt(update: Update, context: CallbackContext):
    user_answer = update.message.text
    answer = get_answer(update.effective_user.id, context)

    if user_answer.lower() == answer.lower():
        context.user_data['score'] += 1
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


def get_score(update: Update, context: CallbackContext):
    update.message.reply_text(f'Счёт {context.user_data["score"]}')
    return State.CHOOSE


def end_quiz(update: Update, context: CallbackContext):
    update.message.reply_text(
        f'Спасибо за игру! Финальный счёт {context.user_data["score"]}'
    )
    return ConversationHandler.END


if __name__ == '__main__':
    env = Env()
    env.read_env()

    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO)

    tg_bot_token = env.str('TG_BOT_TOKEN')
    db_endpoint = env.str('DB_ENDPOINT')
    db_port = env.int('DB_PORT')
    db_password = env.str('DB_PASSWORD')

    redis_db = setup_redis_db(db_endpoint, db_port, db_password)

    updater = Updater(tg_bot_token)
    dispatcher = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler('start', partial(start, redis_db=redis_db))],

        states={
            State.CHOOSE: [
                MessageHandler(
                    Filters.text(NEW_QUESTION_TEXT),
                    send_new_question,
                    pass_user_data=True
                ),
                MessageHandler(
                    Filters.text(GET_SCORE_TEXT),
                    get_score,
                    pass_user_data=True
                ),
            ],

            State.ENTER_ANSWER: [
                MessageHandler(
                    Filters.text(GIVE_UP_TEXT),
                    send_answer,
                    pass_user_data=True
                ),
                MessageHandler(
                    Filters.text(GET_SCORE_TEXT),
                    get_score,
                    pass_user_data=True
                ),
                MessageHandler(
                Filters.text & ~Filters.command,
                handle_solution_attempt,
                pass_user_data=True
                ),
            ],
        },

        fallbacks=[CommandHandler('finish', end_quiz, pass_user_data=True)]
    )

    dispatcher.add_handler(conv_handler)

    while True:
        try:
            updater.start_polling()
            updater.idle()
        except Exception as err:
            logger.exception(f"⚠ Ошибка бота:\n\n {err}")
            sleep(60)

