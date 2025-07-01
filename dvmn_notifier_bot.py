import logging
import time

import environs
import requests
import telegram

LONG_POLLING_URL = 'https://dvmn.org/api/long_polling/'
logger = logging.getLogger('telegram_logger')


class TelegramLogsHandler(logging.Handler):
    def __init__(self, log_token, chat_id):
        super().__init__()
        self.tg_chat_id = chat_id
        self.log_tg_bot = telegram.Bot(token=log_token)

    def emit(self, record):
        log_entry = self.format(record)
        self.log_tg_bot.send_message(
            text=log_entry, chat_id=self.tg_chat_id
        )


def get_long_polling_response(
        devman_token: str,
        tg_bot,
        chat_id: str,
        timestamp: float,
        long_polling_url=LONG_POLLING_URL
) -> float:
    headers = {
        'Authorization': f'Token {devman_token}',
    }
    payload = {
        'timestamp': timestamp,
    }
    response = requests.get(
        long_polling_url, headers=headers, params=payload, timeout=120
    )
    response.raise_for_status()
    response = response.json()

    if response.get('status') == 'timeout':
        timestamp = response.get('timestamp_to_request')
    elif response.get('status') == 'found':
        timestamp = response.get('last_attempt_timestamp')
        new_attempts = response.get('new_attempts')[0]
        lesson_title = new_attempts.get('lesson_title')
        verification_status = new_attempts.get('is_negative')
        lesson_url = new_attempts.get('lesson_url')
        send_message(
            lesson_title,
            verification_status,
            lesson_url,
            tg_bot,
            chat_id
        )
    return timestamp


def send_message(
        lesson_title: str,
        verification_status: bool,
        lesson_url: str,
        tg_bot,
        chat_id: str
) -> None:
    if verification_status:
        tg_bot.send_message(
            text=f'У вас проверили работу «{lesson_title}»!\n\n'
                 f'К сожалению, в работе нашлись ошибки.'
                 f'\nСсылка на работу: {lesson_url}',
            chat_id=chat_id,
        )
    else:
        tg_bot.send_message(
            text=f'У вас проверили работу «{lesson_title}»!\n\n'
                 f'Преподавателю все понравилось, можно приступать '
                 f'к следующему уроку.\n'
                 f'Ссылка на работу: {lesson_url}',
            chat_id=chat_id,
        )


if __name__ == '__main__':
    env = environs.Env()
    env.read_env()
    devman_api_token = env('DEVMAN_TOKEN')
    tg_token = env('TG_TOKEN')
    tg_log_token = env('TG_LOG_BOT_TOKEN')
    tg_chat_id = env('TG_CHAT_ID')

    logger.setLevel(level=logging.DEBUG)
    log_handler = TelegramLogsHandler(tg_log_token, tg_chat_id)
    logger.addHandler(log_handler)

    notification_tg_bot = telegram.Bot(token=tg_token)
    now_timestamp = time.time()

    while True:
        try:
            now_timestamp = get_long_polling_response(
                devman_api_token,
                notification_tg_bot,
                tg_chat_id,
                now_timestamp
            )
        except requests.exceptions.ReadTimeout:
            continue
        except requests.exceptions.HTTPError as err:
            logger.error(f'Бот упал с ошибкой:\n {err}', exc_info=True)
        except requests.exceptions.ConnectionError:
            logger.warning(
                'Не удается подключиться к серверу!'
                ' Повторное подключение через 10 секунд.'
            )
            time.sleep(10)
            continue
