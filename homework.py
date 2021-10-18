import logging
import os
import time

import requests
from dotenv import load_dotenv
from telegram import Bot

load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
CONSTANTS_AUTH = [PRACTICUM_TOKEN, TELEGRAM_TOKEN, CHAT_ID]
RETRY_TIME = 5
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)

if not all(CONSTANTS_AUTH):
    logging.critical(' Отсутствует обязательная переменная окружения')
    exit()


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена, в ней нашлись ошибки.'
}


class TheAnswerIsNot200Error(Exception):
    pass


class TheParseStatusIsVacuum(Exception):
    pass


class TheResponseUnknownStatus(Exception):
    pass


def send_message(bot, message):
    try:
        message = bot.send_message(CHAT_ID, message)
        logging.info('Удачная отправка сообщения в Telegram')
    except Exception as error:
        logging.error('Сбой при отправке сообщения в Telegram: '
                      f'{error}')
    return message


def get_api_answer(url, current_timestamp):
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
    try:
        verdict = HOMEWORK_STATUSES.get(homework.get('status'))
        homework_name = homework.get('homework_name')
        return (
            f'Изменился статус проверки работы "{homework_name}". {verdict}')
    except KeyError as error:
        logging.error(error)


def check_response(response):
    homework = response.get('homeworks')
    if homework == []:
        raise TheResponseUnknownStatus('Ревьюер твою домашку еще не получал')
    homework = homework[0]
    verdict = HOMEWORK_STATUSES.get(homework.get('status'))
    if verdict is None:
        raise TheParseStatusIsVacuum('Не известный статус')
    return homework


def main():
    bot = Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    while True:
        try:
            response = get_api_answer(ENDPOINT, current_timestamp)
            homework = check_response(response)
            send_message(bot, parse_status(homework))
            time.sleep(RETRY_TIME)
            current_timestamp = int(time.time() - 600)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(message)
            time.sleep(RETRY_TIME)
            current_timestamp = int(time.time() - 600)
            continue


if __name__ == '__main__':
    main()
