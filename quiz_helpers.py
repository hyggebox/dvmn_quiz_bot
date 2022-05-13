import os
import re

import redis


NEW_QUESTION_TEXT = 'Новый вопрос'
GIVE_UP_TEXT = 'Показать ответ'
GET_SCORE_TEXT = 'Мой счёт'


def get_questions():
    for filename in os.listdir('quiz-questions'):
        with open(f'quiz-questions/{filename}', 'r', encoding='KOI8-R') as question_file:
            file_contents = question_file.read()
        split_contents = file_contents.split("\n\n")

        question_answer_pairs = {}
        qa_pair = []
        for content_part in split_contents:
            if 'Вопрос' in content_part and not qa_pair:
                qa_pair.append(content_part.split(':', 1)[1])
            if 'Ответ:' in content_part and len(qa_pair) == 1:
                qa_pair.append(re.sub(
                    '[\(\[].*?[\)\]]', '', content_part.removeprefix('Ответ:')
                        .replace('... ', '')
                        .replace('"', '')
                        .split('.')[0]
                        .strip()
                ))
            if len(qa_pair) == 2:
                question_answer_pairs[qa_pair[0]] = qa_pair[1]
                qa_pair.clear()

    return question_answer_pairs


def setup_redis_db(host, port, password):
    try:
        return redis.StrictRedis(host=host, port=port,
                                 password=password,
                                 decode_responses=True)
    except Exception as error:
        print(error)