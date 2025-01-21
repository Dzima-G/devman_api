from dotenv import load_dotenv
import requests
import sys
import time
import logging
import telegram
import os

logger = logging.getLogger(__name__)


def get_long_polling_response(url, devman_token, timestamp):
    headers = {'Authorization': f'Token {devman_token}'}
    while True:
        payload = {'timestamp': timestamp}
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
            send_message(lesson_title, verification_status, lesson_url)


def send_message(lesson_title, verification_status, lesson_url):
    bot = telegram.Bot(token=telegram_token)
    if verification_status:
        bot.send_message(
            text=f'У вас проверили работу «{lesson_title}»!\n\n'
                 f'К сожалению, в работе нашлись ошибки.'
                 f'\nСсылка на работу: {lesson_url}',
            chat_id=telegram_chat_id)
    else:
        bot.send_message(
            text=f'У вас проверили работу «{lesson_title}»!\n\n'
                 f'Преподавателю все понравилось, можно приступать к следующему уроку.\n'
                 f'Ссылка на работу: {lesson_url}',
            chat_id=telegram_chat_id)


if __name__ == "__main__":
    load_dotenv()

    devman_api_token = os.environ['DEVMAN_API_TOKEN']
    telegram_token = os.environ['TELEGRAM_TOKEN']
    telegram_chat_id = os.environ['TG_CHAT_ID']

    url = 'https://dvmn.org/api/long_polling/'
    now_timestamp = time.time()

    while True:
        try:
            get_long_polling_response(url, devman_api_token, now_timestamp)
        except requests.exceptions.ReadTimeout:
            continue
        except requests.exceptions.HTTPError as error:
            print(error, file=sys.stderr)
        except requests.exceptions.ConnectionError:
            logger.warning(f'Не удается подключиться к серверу! Повторное подключение через 10 секунд.')
            time.sleep(10)
            continue
