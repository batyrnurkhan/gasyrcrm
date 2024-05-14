from django.conf import settings
from django.conf.urls.static import static
from django.urls import path

from subjects.views import create_task
from .views import chat_room_list, chat_room_detail
app_name = 'chats'

urlpatterns = [
    path('rooms/', chat_room_list, name='chat_room_list'),
    path('rooms/<int:room_id>/', chat_room_detail, name='chat_room_detail'),
    path('rooms/<int:room_id>/tasks/', create_task, name='create_task'),

              ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)