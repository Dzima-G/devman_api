from dotenv import load_dotenv
import requests
import sys
import time
import logging
import asyncio
import telegram
import os

logger = logging.getLogger(__name__)


def get_long_polling_response(url, devman_token, timestamp):
    headers = {'Authorization': f'Token {devman_token}'}
    while True:
        payload = {'timestamp': timestamp}
        response = requests.get(url, headers=headers, params=payload)
        response.raise_for_status()
        if response.json().get('status') in 'timeout':
            timestamp = response.json().get('timestamp_to_request')
        elif response.json().get('status') in 'found':
            timestamp = response.json().get('last_attempt_timestamp')
            data = response.json().get('new_attempts')[0]
            lesson_title = data.get('lesson_title')
            verification_status = data.get('is_negative')
            lesson_url = data.get('lesson_url')
            asyncio.run(send_message(lesson_title, verification_status, lesson_url))


async def send_message(lesson_title, verification_status, lesson_url):
    bot = telegram.Bot(telegram_token)
    async with bot:
        if verification_status:
            await bot.send_message(
                text=f'У вас проверили работу «{lesson_title}»!\n\n'
                     f'К сожалению, в работе нашлись ошибки.'
                     f'\nСсылка на работу: {lesson_url}',
                chat_id=telegram_chat_id)
        else:
            await bot.send_message(
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
            logger.warning(f'Server timed out! Reload!')
            continue
        except requests.exceptions.HTTPError as error:
            print(error, file=sys.stderr)
        except requests.exceptions.ConnectionError:
            logger.warning(f'Не удается подключиться к серверу! Повторное подключение через 10 секунд.')
            time.sleep(10)
            continue
