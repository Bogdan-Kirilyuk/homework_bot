import logging
import os
import time

import requests
from dotenv import load_dotenv
from telegram import Bot

load_dotenv()


PRACTICUM_TOKEN = os.getenv(
    'PRACTICUM_TOKEN', default="SUP3R-S3CR3T-K3Y-F0R-MY-PR0J3CT")
TELEGRAM_TOKEN = os.getenv(
    'TELEGRAM_TOKEN', default="SUP3R-S3CR3T-K3Y-F0R-MY-PR0J3CT")
CHAT_ID = os.getenv('CHAT_ID', default="SUP3R-S3CR3T-K3Y-F0R-MY-PR0J3CT")
CONST_AUTH = [PRACTICUM_TOKEN, TELEGRAM_TOKEN, CHAT_ID]
RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена, в ней нашлись ошибки.'
}

if not all(CONST_AUTH):
    logging.critical(' Отсутствует обязательная переменная окружения')
    exit()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)


# if not all(CONSTANTS_AUTH):
#     logging.critical(' Отсутствует обязательная переменная окружения')
#     exit()


class TheAnswerIsNot200Error(Exception):
    """Перехват исключения - эндпоинт не доступен."""

    pass


class TheParseStatusIsVacuum(Exception):
    """Перехват исключения - недокументированный статус."""

    pass


class TheResponseUnknownStatus(Exception):
    """Перехват исключения - отсутствует ключ homeworks."""

    pass


def send_message(bot, message):
    """Отправка сообщения в телеграм."""
    try:
        message = bot.send_message(CHAT_ID, message)
        logging.info('Удачная отправка сообщения в Telegram')
    except Exception as error:
        logging.error('Сбой при отправке сообщения в Telegram: '
                      f'{error}')
    return message


def get_api_answer(url, current_timestamp):
    """Получение ответа с API яндекс.практикум."""
    headers = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}
    payload = {'from_date': current_timestamp}
    homework_statuses = requests.get(url, headers=headers, params=payload)
    response = homework_statuses
    if response.status_code != 200:
        raise TheAnswerIsNot200Error(
            f'Эндпоинт {ENDPOINT} недоступен. '
            f'Код ответа API: {response.status_code}')
    response = response.json()
    return response


def parse_status(homework):
    """Анализ статуса проверки домашки."""
    try:
        verdict = HOMEWORK_STATUSES.get(homework.get('status'))
        homework_name = homework.get('homework_name')
        return (
            f'Изменился статус проверки работы "{homework_name}". {verdict}')
    except KeyError as error:
        logging.error(error)


def check_response(response):
    """Проверка, что домашку взяли на ревью."""
    homework = response.get('homeworks')
    if homework == []:
        raise TheResponseUnknownStatus(
            'Отсутствует ключ homeworks или домашку не взяли в ревью')
    homework = homework[0]
    verdict = HOMEWORK_STATUSES.get(homework.get('status'))
    if verdict is None:
        logging.error('Ошибка недокументированный статус')

        raise TheParseStatusIsVacuum('Ошибка - недокументированный статус')
    return homework


def main():
    """Основная функция запуска бота."""
    bot = Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time()) - 600
    while True:
        try:
            response = get_api_answer(ENDPOINT, current_timestamp)
            homework = check_response(response)
            send_message(bot, parse_status(homework))
            time.sleep(RETRY_TIME)
            current_timestamp = int(time.time()) - 600
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            send_message(bot, message)
            logging.error(message)
            time.sleep(RETRY_TIME)
            current_timestamp = int(time.time()) - 600
            continue


if __name__ == '__main__':
    main()
