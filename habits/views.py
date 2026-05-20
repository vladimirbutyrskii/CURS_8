from rest_framework import viewsets, generics, status
from rest_framework.permissions import IsAuthenticated
from .models import Habit, TelegramUser

from .permissions import IsOwner
from .pagination import HabitPagination

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from rest_framework.response import Response

from .serializers import (
    HabitSerializer,
    HabitCreateSerializer,
    HabitUpdateSerializer,
    TelegramUserSerializer,
)


class HabitViewSet(viewsets.ModelViewSet):
    """
    CRUD для привычек текущего пользователя.

    Доступные действия:
    - list: список привычек пользователя (пагинация по 5)
    - create: создание новой привычки
    - retrieve: детальный просмотр привычки
    - update: полное обновление привычки
    - partial_update: частичное обновление привычки
    - destroy: удаление привычки
    """

    serializer_class = HabitSerializer
    permission_classes = [IsAuthenticated, IsOwner]
    pagination_class = HabitPagination

    def get_serializer_class(self):
        if self.action == 'create':
            return HabitCreateSerializer
        elif self.action in ('update', 'partial_update'):
            return HabitUpdateSerializer
        return HabitSerializer

    def get_queryset(self):
        """Только привычки текущего пользователя."""
        return Habit.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        """Подстановка текущего пользователя при создании."""
        serializer.save(user=self.request.user)


class PublicHabitListView(generics.ListAPIView):
    """
    Список публичных привычек (только чтение).

    Возвращает привычки с признаком is_public=True,
    исключая привычки текущего пользователя.
    Пагинация по 5.
    """

    # serializer_class = HabitSerializer
    # permission_classes = [IsAuthenticated]
    # pagination_class = HabitPagination

    def get_queryset(self):
        """Только публичные привычки, исключая привычки текущего пользователя."""
        return Habit.objects.filter(is_public=True).exclude(user=self.request.user)


class TelegramLinkView(generics.CreateAPIView):
    """
    Привязка Telegram-аккаунта к пользователю.

    Принимает chat_id, создаёт или обновляет связь User ↔ TelegramUser.
    """

    serializer_class = TelegramUserSerializer
    # permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['chat_id'],
            properties={
                'chat_id': openapi.Schema(type=openapi.TYPE_STRING, description='Chat ID пользователя в Telegram'),
            },
        ),
        responses={
            201: TelegramUserSerializer,
            200: TelegramUserSerializer,
        }
    )
    def create(self, request, *args, **kwargs):
        chat_id = request.data.get('chat_id')
        if not chat_id:
            return Response(
                {'error': 'chat_id обязателен'},
                status=status.HTTP_400_BAD_REQUEST
            )

        telegram_user, created = TelegramUser.objects.update_or_create(
            user=request.user,
            defaults={'chat_id': chat_id, 'is_active': True}
        )

        return Response(
            TelegramUserSerializer(telegram_user).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
        )
