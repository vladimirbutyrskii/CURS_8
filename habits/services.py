import requests
from django.conf import settings


def send_telegram_message(chat_id, text):
    """Отправка сообщения через Telegram Bot API."""

    token = settings.TELEGRAM_BOT_TOKEN
    if not token:
        raise ValueError('TELEGRAM_BOT_TOKEN не настроен в .env')

    url = f'https://api.telegram.org/bot{token}/sendMessage'
    payload = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': 'HTML',
    }

    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        # Логирование ошибки (будет улучшено в следующих разделах)
        print(f'Ошибка отправки сообщения в Telegram: {e}')
        return None


def build_reminder_message(habit):
    """Формирование текста напоминания."""

    time_str = habit.time.strftime('%H:%M')

    message = (
        f'🔔 <b>Пора выполнить привычку!</b>\n\n'
        f'<b>Действие:</b> {habit.action}\n'
        f'<b>Место:</b> {habit.place}\n'
        f'<b>Время:</b> {time_str}\n'
    )

    if habit.reward:
        message += f'\n🎁 <b>Вознаграждение:</b> {habit.reward}'
    elif habit.linked_habit:
        message += f'\n🎁 <b>Приятная привычка:</b> {habit.linked_habit.action}'

    return message
