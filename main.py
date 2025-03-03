import logging
import os
import sys
import time

import requests
import telegram
from dotenv import load_dotenv


class TelegramLogsHandler(logging.Handler):

    def __init__(self, tg_bot, chat_id):
        super().__init__()
        self.chat_id = chat_id
        self.tg_bot = tg_bot

    def emit(self, record):
        log_entry = self.format(record)
        self.tg_bot.send_message(chat_id=self.chat_id, text=log_entry)


def get_long_polling_response(url, devman_token, timestamp, tg_bot):
    headers = {
        'Authorization': f'Token {devman_token}',
    }
    while True:
        payload = {
            'timestamp': timestamp,
        }
        response = requests.get(url, headers=headers, params=payload)
        response.raise_for_status()
        response = response.json()
        if response.get('status') in 'timeout':
            timestamp = response.get('timestamp_to_request')
        elif response.get('status') in 'found':
            timestamp = response.get('last_attempt_timestamp')
            new_attempts = response.get('new_attempts')[0]
            lesson_title = new_attempts.get('lesson_title')
            verification_status = new_attempts.get('is_negative')
            lesson_url = new_attempts.get('lesson_url')
            send_message(lesson_title, verification_status, lesson_url, tg_bot)


def send_message(lesson_title, verification_status, lesson_url, tg_bot):
    if verification_status:
        tg_bot.send_message(
            text=f'У вас проверили работу «{lesson_title}»!\n\n'
                 f'К сожалению, в работе нашлись ошибки.'
                 f'\nСсылка на работу: {lesson_url}',
            chat_id=telegram_chat_id)
    else:
        tg_bot.send_message(
            text=f'У вас проверили работу «{lesson_title}»!\n\n'
                 f'Преподавателю все понравилось, можно приступать '
                 f'к следующему уроку.\n'
                 f'Ссылка на работу: {lesson_url}',
            chat_id=telegram_chat_id)


if __name__ == "__main__":
    load_dotenv()

    devman_api_token = os.environ['DEVMAN_API_TOKEN']
    telegram_token = os.environ['TELEGRAM_TOKEN']
    telegram_chat_id = os.environ['TG_CHAT_ID']

    telegram_bot = telegram.Bot(token=telegram_token)

    logger = logging.getLogger('Logger')
    logging.basicConfig(level=logging.INFO)
    logger.addHandler(TelegramLogsHandler(telegram_bot, telegram_chat_id))

    url = 'https://dvmn.org/api/long_polling/'
    now_timestamp = time.time()

    while True:
        try:
            logger.info('Бот запущен')
            get_long_polling_response(
                url,
                devman_api_token,
                now_timestamp,
                telegram_bot)
        except requests.exceptions.ReadTimeout:
            logger.warning('Ожидание ответа от сервера истекло,'
                           'повторный запрос отправлен!')
            continue
        except requests.exceptions.HTTPError as error:
            logger.error('Бот упал с ошибкой:')
            print(error, file=sys.stderr)
        except requests.exceptions.ConnectionError:

            logger.warning('Не удается подключиться к серверу!'
                           ' Повторное подключение через 10 секунд.')
            time.sleep(10)
            continue
        except Exception as err:
            logger.error('Бот упал с ошибкой:')
            logger.exception(err)
            break
