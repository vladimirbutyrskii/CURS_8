import pytest
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from habits.models import Habit, TelegramUser


@pytest.mark.django_db
class TestHabitModel:

    def test_create_valid_habit(self):
        """Создание полезной привычки с вознаграждением."""
        user = User.objects.create_user(username='test@test.ru', email='test@test.ru', password='test1234')
        habit = Habit.objects.create(
            user=user,
            place='Дом',
            time='08:00',
            action='Зарядка',
            is_pleasant=False,
            periodicity=1,
            reward='Кофе',
            duration=60,
            is_public=False
        )
        assert habit.action == 'Зарядка'
        assert habit.reward == 'Кофе'

    def test_create_pleasant_habit(self):
        """Создание приятной привычки."""
        user = User.objects.create_user(username='test@test.ru', email='test@test.ru', password='test1234')
        habit = Habit.objects.create(
            user=user,
            place='Дом',
            time='20:00',
            action='Чтение книги',
            is_pleasant=True,
            periodicity=1,
            duration=120,
            is_public=False
        )
        assert habit.is_pleasant is True
        assert habit.reward is None
        assert habit.linked_habit is None

    def test_linked_habit_must_be_pleasant(self):
        """Связанная привычка должна быть приятной."""
        user = User.objects.create_user(username='test@test.ru', email='test@test.ru', password='test1234')
        not_pleasant = Habit.objects.create(
            user=user, place='Дом', time='09:00', action='Обычная',
            is_pleasant=False, periodicity=1, duration=60
        )
        with pytest.raises(ValidationError):
            Habit.objects.create(
                user=user, place='Работа', time='10:00', action='Полезная',
                is_pleasant=False, linked_habit=not_pleasant, periodicity=1, duration=60
            )

    def test_cannot_have_both_reward_and_linked(self):
        """Нельзя одновременно указать вознаграждение и связанную привычку."""
        user = User.objects.create_user(username='test@test.ru', email='test@test.ru', password='test1234')
        pleasant = Habit.objects.create(
            user=user, place='Дом', time='21:00', action='Ванна',
            is_pleasant=True, periodicity=1, duration=60
        )
        with pytest.raises(ValidationError):
            Habit.objects.create(
                user=user, place='Дом', time='08:00', action='Прогулка',
                is_pleasant=False, linked_habit=pleasant, reward='Шоколад',
                periodicity=1, duration=60
            )

    def test_duration_validation(self):
        """Время выполнения не больше 120 секунд."""
        user = User.objects.create_user(username='test@test.ru', email='test@test.ru', password='test1234')
        with pytest.raises(ValidationError):
            Habit.objects.create(
                user=user, place='Дом', time='08:00', action='Длинная',
                is_pleasant=False, periodicity=1, duration=200
            )

    def test_periodicity_validation(self):
        """Периодичность от 1 до 7 дней."""
        user = User.objects.create_user(username='test@test.ru', email='test@test.ru', password='test1234')
        with pytest.raises(ValidationError):
            Habit.objects.create(
                user=user, place='Дом', time='08:00', action='Редкая',
                is_pleasant=False, periodicity=10, duration=60
            )

    def test_pleasant_habit_no_reward_or_linked(self):
        """У приятной привычки не может быть вознаграждения или связанной привычки."""
        user = User.objects.create_user(username='test@test.ru', email='test@test.ru', password='test1234')
        with pytest.raises(ValidationError):
            Habit.objects.create(
                user=user, place='Дом', time='20:00', action='Кино',
                is_pleasant=True, reward='Попкорн', periodicity=1, duration=60
            )


@pytest.mark.django_db
class TestTelegramUserModel:

    def test_create_telegram_user(self):
        """Создание привязки Telegram."""
        user = User.objects.create_user(username='test@test.ru', email='test@test.ru', password='test1234')
        telegram_user = TelegramUser.objects.create(user=user, chat_id='123456789')
        assert telegram_user.chat_id == '123456789'
        assert telegram_user.is_active is True

    def test_unique_chat_id(self):
        """Chat ID должен быть уникальным."""
        user1 = User.objects.create_user(username='u1@test.ru', email='u1@test.ru', password='test1234')
        user2 = User.objects.create_user(username='u2@test.ru', email='u2@test.ru', password='test1234')
        TelegramUser.objects.create(user=user1, chat_id='123456789')
        with pytest.raises(Exception):
            TelegramUser.objects.create(user=user2, chat_id='123456789')
