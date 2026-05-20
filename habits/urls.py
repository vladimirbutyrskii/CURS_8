from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import HabitViewSet, PublicHabitListView, TelegramLinkView

router = DefaultRouter()
router.register(r'habits', HabitViewSet, basename='habits')

urlpatterns = [
    path('habits/public/', PublicHabitListView.as_view(), name='public-habits'),
    path('telegram/link/', TelegramLinkView.as_view(), name='telegram-link'),
    path('', include(router.urls)),
]
