from django.db import models
from django.conf import settings

from .validators import validate_duration, validate_periodicity, validate_habit


class Habit(models.Model):
    """Модель привычки."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='habits',
        verbose_name='Пользователь'
    )
    place = models.CharField(
        max_length=255,
        verbose_name='Место выполнения'
    )
    time = models.TimeField(
        verbose_name='Время выполнения'
    )
    action = models.CharField(
        max_length=255,
        verbose_name='Действие'
    )
    is_pleasant = models.BooleanField(
        default=False,
        verbose_name='Признак приятной привычки'
    )
    linked_habit = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='linked_to',
        verbose_name='Связанная привычка'
    )
    periodicity = models.PositiveIntegerField(
        default=1,
        validators=[validate_periodicity],  # Правило 5
        verbose_name='Периодичность (в днях)'
    )
    reward = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name='Вознаграждение'
    )
    duration = models.PositiveIntegerField(
        default=120,
        validators=[validate_duration],  # Правило 2
        verbose_name='Время на выполнение (в секундах)'
    )
    is_public = models.BooleanField(
        default=False,
        verbose_name='Признак публичности'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата обновления'
    )

    class Meta:
        verbose_name = 'Привычка'
        verbose_name_plural = 'Привычки'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user}: {self.action} в {self.place} в {self.time}'

    def clean(self):
        """Вызов всех валидаторов модели."""
        super().clean()
        validate_habit(self)  # Правила 1, 3, 4

    def save(self, *args, **kwargs):
        """Гарантированный вызов clean() перед сохранением."""
        self.full_clean()
        super().save(*args, **kwargs)


class TelegramUser(models.Model):
    """Связь пользователя с Telegram-аккаунтом."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='telegram_user',
        verbose_name='Пользователь'
    )
    chat_id = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='Chat ID Telegram'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Активен'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата привязки'
    )

    class Meta:
        verbose_name = 'Telegram-пользователь'
        verbose_name_plural = 'Telegram-пользователи'

    def __str__(self):
        return f'{self.user.email} — {self.chat_id}'
