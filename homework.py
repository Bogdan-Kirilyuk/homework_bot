import logging
import os
import time

import requests
from dotenv import load_dotenv
from telegram import Bot
from telegram.error import TelegramError

load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv(
    'TELEGRAM_TOKEN', default="SUP3R-S3CR3T-K3Y-F0R-MY-PR0J3CT")
CHAT_ID = os.getenv('CHAT_ID', default="SUP3R-S3CR3T-K3Y-F0R-MY-PR0J3CT")
RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена, в ней нашлись ошибки.'
}


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)


class TheAnswerIsNot200Error(Exception):
    """Перехват исключения - эндпоинт не доступен."""

    pass


class TheParseStatusUnknow(Exception):
    """Перехват исключения - недокументированный статус."""

    pass


class TheResponseUnknownKey(Exception):
    """Перехват исключения - отсутствует ключ в запросе."""

    pass


def check_constant_auth():
    """Проверка наличия обязательных переменных для работы бота."""
    if not PRACTICUM_TOKEN:
        logging.critical(
            'Отсутствует обязательная переменная окружения PRACTICUM_TOKEN')
        exit()
    elif not TELEGRAM_TOKEN:
        logging.critical(
            'Отсутствует обязательная переменная окружения TELEGRAM_TOKEN')
        exit()
    elif not CHAT_ID:
        logging.critical(
            'Отсутствует обязательная переменная окружения CHAT_ID')
        exit()


def send_message(bot, message):
    """Отправка сообщения в телеграм."""
    try:
        message = bot.send_message(CHAT_ID, message)
        logging.info('Удачная отправка сообщения в Telegram')
    except TelegramError as error:
        logging.error('Сбой при отправке сообщения в Telegram: '
                      f'{error}')


def get_api_answer(url, current_timestamp):
    """Получение ответа с API яндекс.практикум."""
    headers = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}
    payload = {'from_date': current_timestamp}
    try:
        response = requests.get(url, headers=headers, params=payload)
        if response.status_code != 200:
            raise TheAnswerIsNot200Error(
                f'Эндпоинт {ENDPOINT} недоступен. '
                f'Код ответа API: {response.status_code}')
        return response.json()
    except requests.RequestException as error:
        logging.error(f'Проблемы с запросом {error}')
    except ValueError as error:
        logging.error(f'Недопустимое значение {error}')


def parse_status(homework):
    """Анализ статуса проверки домашки."""
    status = homework.get('status')
    verdict = HOMEWORK_STATUSES.get(status)
    homework_name = homework.get('homework_name')
    if (homework_name or status) is None:
        raise TheResponseUnknownKey(
            'Отсутствует ключ homework_name или status')
    return (
        f'Изменился статус проверки работы "{homework_name}". {verdict}')


def check_response(response):
    """Проверка, что домашку взяли на ревью."""
    homework = response.get('homeworks')
    if (homework is None) or (type(homework) != list):
        raise TheResponseUnknownKey(
            'Отсутствует ключ homeworks или homeworks не правильного типа')
    if homework == []:
        return False
    homework = homework[0]
    status = homework.get('status')
    if status in HOMEWORK_STATUSES:
        return homework
    raise TheParseStatusUnknow('Нет такого статуса')


def main():
    """Основная функция запуска бота."""
    check_constant_auth()
    bot = Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    send_error = True
    while True:
        try:
            response = get_api_answer(ENDPOINT, current_timestamp)
            if check_response(response) is False:
                send_message(bot, 'Домашку не взяли на ревью')
                time.sleep(RETRY_TIME)
            else:
                homework = check_response(response)
                message = parse_status(homework)
                send_message(bot, message)
                current_timestamp = response.get('current_date')
                time.sleep(RETRY_TIME)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            if send_error:
                send_message(bot, message)
                send_error = False
            logging.error(message)
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
