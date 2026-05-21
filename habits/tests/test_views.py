import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from habits.models import Habit


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user():
    return User.objects.create_user(username='test@test.ru', email='test@test.ru', password='test1234')


@pytest.fixture
def another_user():
    return User.objects.create_user(username='other@test.ru', email='other@test.ru', password='test1234')


@pytest.fixture
def auth_client(api_client, user):
    """Клиент с JWT-авторизацией."""
    refresh = RefreshToken.for_user(user)
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    return api_client


@pytest.fixture
def another_auth_client(api_client, another_user):
    """Клиент второго пользователя."""
    refresh = RefreshToken.for_user(another_user)
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    return api_client


@pytest.fixture
def habit(user):
    return Habit.objects.create(
        user=user, place='Дом', time='08:00', action='Зарядка',
        is_pleasant=False, periodicity=1, reward='Кофе', duration=60
    )


@pytest.fixture
def pleasant_habit(user):
    return Habit.objects.create(
        user=user, place='Дом', time='21:00', action='Чтение',
        is_pleasant=True, periodicity=1, duration=60
    )


@pytest.fixture
def public_habit(another_user):
    return Habit.objects.create(
        user=another_user, place='Парк', time='07:00', action='Бег',
        is_pleasant=False, periodicity=1, reward='Смузи', duration=60, is_public=True
    )


@pytest.mark.django_db
class TestHabitCRUD:

    def test_create_habit(self, auth_client):
        """Создание привычки текущим пользователем."""
        data = {
            'place': 'Зал',
            'time': '18:00',
            'action': 'Тренировка',
            'is_pleasant': False,
            'periodicity': 2,
            'reward': 'Протеин',
            'duration': 90
        }
        response = auth_client.post('/api/habits/', data)
        assert response.status_code == 201
        assert response.data['action'] == 'Тренировка'

    def test_list_own_habits(self, auth_client, habit):
        """Список своих привычек."""
        response = auth_client.get('/api/habits/')
        assert response.status_code == 200
        assert 'results' in response.data
        assert len(response.data['results']) >= 1

    def test_retrieve_own_habit(self, auth_client, habit):
        """Детальный просмотр своей привычки."""
        response = auth_client.get(f'/api/habits/{habit.id}/')
        assert response.status_code == 200
        assert response.data['action'] == 'Зарядка'

    def test_update_habit(self, auth_client, habit):
        """Обновление своей привычки."""
        data = {'action': 'Утренняя зарядка'}
        response = auth_client.patch(f'/api/habits/{habit.id}/', data)
        assert response.status_code == 200
        assert response.data['action'] == 'Утренняя зарядка'

    def test_delete_habit(self, auth_client, habit):
        """Удаление своей привычки."""
        response = auth_client.delete(f'/api/habits/{habit.id}/')
        assert response.status_code == 204

    def test_cannot_access_other_user_habit(self, auth_client, public_habit):
        """Нельзя получить доступ к чужой привычке через CRUD."""
        response = auth_client.get(f'/api/habits/{public_habit.id}/')
        assert response.status_code == 404

    def test_cannot_update_other_user_habit(self, auth_client, public_habit):
        """Нельзя обновить чужую привычку."""
        data = {'action': 'Взлом'}
        response = auth_client.patch(f'/api/habits/{public_habit.id}/', data)
        assert response.status_code == 404


@pytest.mark.django_db
class TestPublicHabits:

    def test_list_public_habits(self, auth_client, public_habit):
        """Получение списка публичных привычек."""
        response = auth_client.get('/api/habits/public/')
        assert response.status_code == 200
        habits = response.data
        assert any(h['is_public'] for h in habits)

    def test_public_habits_exclude_own(self, another_auth_client, public_habit):
        """Публичные привычки не включают свои."""
        response = another_auth_client.get('/api/habits/public/')
        assert response.status_code == 200
        # public_habit принадлежит another_user, поэтому его не будет в выдаче для него
        results_ids = [h['id'] for h in response.data]
        assert public_habit.id not in results_ids

    def test_cannot_modify_public_habit(self, auth_client, public_habit):
        """Нельзя удалить публичную привычку (она чужая)."""
        response = auth_client.delete(f'/api/habits/{public_habit.id}/')
        assert response.status_code == 404


@pytest.mark.django_db
class TestPagination:

    def test_pagination_structure(self, auth_client, habit):
        """Проверка структуры пагинации."""
        response = auth_client.get('/api/habits/')
        assert response.status_code == 200
        assert 'count' in response.data
        assert 'next' in response.data
        assert 'previous' in response.data
        assert 'results' in response.data
        assert isinstance(response.data['results'], list)


@pytest.mark.django_db
class TestAuth:

    def test_register_user(self, api_client):
        """Регистрация нового пользователя."""
        data = {
            'email': 'new@test.ru',
            'password': 'strongpass123',
            'password_confirmation': 'strongpass123'
        }
        response = api_client.post('/api/register/', data)
        assert response.status_code == 201
        assert 'access' in response.data
        assert 'refresh' in response.data

    def test_register_password_mismatch(self, api_client):
        """Пароли не совпадают."""
        data = {
            'email': 'new@test.ru',
            'password': 'strongpass123',
            'password_confirmation': 'different'
        }
        response = api_client.post('/api/register/', data)
        assert response.status_code == 400

    def test_login(self, api_client, user):
        """Получение JWT-токенов."""
        data = {'username': 'test@test.ru', 'password': 'test1234'}
        response = api_client.post('/api/token/', data)
        assert response.status_code == 200
        assert 'access' in response.data

    def test_unauthenticated_access(self, api_client):
        """Неавторизованный доступ запрещён."""
        response = api_client.get('/api/habits/')
        assert response.status_code == 401


@pytest.mark.django_db
class TestTelegramLink:

    def test_link_telegram(self, auth_client):
        """Привязка Telegram-аккаунта."""
        data = {'chat_id': '123456789'}
        response = auth_client.post('/api/telegram/link/', data)
        assert response.status_code == 201
        assert response.data['chat_id'] == '123456789'

    def test_update_telegram_link(self, auth_client):
        """Обновление привязки Telegram."""
        data1 = {'chat_id': '111111111'}
        auth_client.post('/api/telegram/link/', data1)
        data2 = {'chat_id': '222222222'}
        response = auth_client.post('/api/telegram/link/', data2)
        assert response.status_code == 200
        assert response.data['chat_id'] == '222222222'

    def test_link_requires_auth(self, api_client):
        """Привязка Telegram требует авторизации."""
        response = api_client.post('/api/telegram/link/', {'chat_id': '123'})
        assert response.status_code == 401
