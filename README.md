# Отслеживание проверки заданий
Скрипт для отслеживания проверки заданий учебных курсов Devman и отправки уведомления.

### Как установить
#### Переменные окружения:

Часть настроек проекта берётся из переменных окружения. Чтобы их определить, создайте файл `.env` в корневом каталоге и запишите туда данные в таком формате: `ПЕРЕМЕННАЯ=значение`.

```
.
├── .env
└── main.py
```
Обязательные переменные окружения:
- `DEVMAN_API_TOKEN` - выглядит например: `8c1000452930e000c0000ee82d5e4as76ff717a6h`. См. документацию https://dvmn.org/api/docs/
- `TELEGRAM_TOKEN` - токен выглядит например: `6000000001:ADEeVTKrhmLSBouDAjhT0r9tBG-AW5VU9YG`. См. документацию https://core.telegram.org/bots/faq#how-do-i-create-a-bot
- `TELEGRAM_CHAT_ID` - выглядит например: `1000001234567` Напишите в Telegram специальному боту: https://telegram.me/userinfobot

Python3 должен быть уже установлен. 
Затем используйте `pip` (или `pip3`, есть конфликт с Python2) для установки зависимостей:

```sh
pip install -r requirements.txt
```

### Применение
Скрипт работает из консольной утилиты.

Для запуска скрипта:
```sh
python main.py
```

### Цель проекта

Код написан в образовательных целях на онлайн-курсе для веб-разработчиков [dvmn.org](https://dvmn.org/).