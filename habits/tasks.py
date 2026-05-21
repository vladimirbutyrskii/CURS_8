from celery import shared_task
from django.utils import timezone

from .models import Habit, TelegramUser
from .services import send_telegram_message, build_reminder_message


@shared_task
def send_habit_reminder(habit_id, chat_id):
    """Отправка напоминания о привычке в Telegram."""
    try:
        habit = Habit.objects.get(id=habit_id)
        message = build_reminder_message(habit)
        send_telegram_message(chat_id, message)
    except Habit.DoesNotExist:
        pass  # Привычка удалена
    except Exception as e:
        print(f'Ошибка в задаче send_habit_reminder (habit_id={habit_id}): {e}')


@shared_task
def check_and_send_reminders():
    """Периодическая задача: проверка привычек и отправка напоминаний."""
    now = timezone.now().time()
    today = timezone.now().date()

    # Все привычки, у которых время выполнения — текущая минута (± погрешность)
    habits = Habit.objects.filter(
        time__hour=now.hour,
        time__minute=now.minute,
        is_pleasant=False  # Напоминаем только о полезных привычках
    )

    for habit in habits:
        # Проверка периодичности: нужно ли сегодня напоминать
        if not _should_send_today(habit, today):
            continue

        # Поиск привязанного Telegram-аккаунта
        try:
            telegram_user = TelegramUser.objects.get(user=habit.user, is_active=True)
        except TelegramUser.DoesNotExist:
            continue  # Пользователь не привязал Telegram

        # Отправка напоминания
        send_habit_reminder.delay(habit.id, telegram_user.chat_id)


def _should_send_today(habit, today):
    """Проверка: нужно ли отправлять напоминание сегодня с учётом периодичности."""
    days_since_creation = (today - habit.created_at.date()).days

    if days_since_creation < 0:
        return False

    # Если периодичность = 1 (ежедневно) — отправляем всегда
    # Иначе проверяем кратность дней
    if habit.periodicity == 1:
        return True

    return days_since_creation % habit.periodicity == 0
