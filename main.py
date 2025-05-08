import logging
import os
import time

import requests
import telegram
from dotenv import load_dotenv


class TelegramLogsHandler(logging.Handler):
    def __init__(self, error_telegram_token, telegram_chat_id):
        super().__init__()
        self.tg_chat_id = telegram_chat_id
        self.error_tg_bot = telegram.Bot(token=error_telegram_token)

    def emit(self, record):
        try:
            log_entry = self.format(record)
            self.error_tg_bot.send_message(
                text=log_entry, chat_id=self.tg_chat_id
            )
        except Exception as e:
            print(f"TelegramLogsHandler error: {e}")


def get_long_polling_response(devman_token, timestamp, tg_bot, tg_chat_id):
    headers = {
        "Authorization": f"Token {devman_token}",
    }
    payload = {
        "timestamp": timestamp,
    }
    response = requests.get(
        "https://dvmn.org/api/long_polling/", headers=headers, params=payload
    )
    response.raise_for_status()
    response = response.json()

    if response.get("status") == "timeout":
        timestamp = response.get("timestamp_to_request")
    elif response.get("status") == "found":
        timestamp = response.get("last_attempt_timestamp")
        new_attempts = response.get("new_attempts")[0]
        lesson_title = new_attempts.get("lesson_title")
        verification_status = new_attempts.get("is_negative")
        lesson_url = new_attempts.get("lesson_url")
        send_message(
            lesson_title,
            verification_status,
            lesson_url,
            tg_bot,
            tg_chat_id,
        )
    return timestamp


def send_message(
    lesson_title, verification_status, lesson_url, tg_bot, tg_chat_id
):
    if verification_status:
        tg_bot.send_message(
            text=f"У вас проверили работу «{lesson_title}»!\n\n"
            f"К сожалению, в работе нашлись ошибки."
            f"\nСсылка на работу: {lesson_url}",
            chat_id=tg_chat_id,
        )
    else:
        tg_bot.send_message(
            text=f"У вас проверили работу «{lesson_title}»!\n\n"
            f"Преподавателю все понравилось, можно приступать "
            f"к следующему уроку.\n"
            f"Ссылка на работу: {lesson_url}",
            chat_id=tg_chat_id,
        )


if __name__ == "__main__":
    load_dotenv()

    devman_api_token = os.environ["DEVMAN_API_TOKEN"]
    telegram_token = os.environ["TELEGRAM_TOKEN"]
    error_telegram_token = os.environ["ERROR_TELEGRAM_TOKEN"]
    telegram_chat_id = os.environ["TG_CHAT_ID"]

    telegram_bot = telegram.Bot(token=telegram_token)

    logger = logging.getLogger("logger")
    logger.setLevel(logging.INFO)
    tg_handler = TelegramLogsHandler(error_telegram_token, telegram_chat_id)
    tg_handler.setLevel(logging.INFO)
    formatter = logging.Formatter("%(message)s")
    tg_handler.setFormatter(formatter)
    logger.addHandler(tg_handler)

    logger.info("Бот успешно запущен!")
    now_timestamp = time.time()

    while True:
        try:
            now_timestamp = get_long_polling_response(
                devman_api_token,
                now_timestamp,
                telegram_bot,
                telegram_chat_id,
            )
        except requests.exceptions.ReadTimeout:
            continue
        except requests.exceptions.HTTPError as err:
            logger.error(f"Бот упал с ошибкой:\n {err}", exc_info=True)
        except requests.exceptions.ConnectionError:
            logger.warning(
                "Не удается подключиться к серверу!"
                " Повторное подключение через 10 секунд."
            )
            time.sleep(10)
            continue
