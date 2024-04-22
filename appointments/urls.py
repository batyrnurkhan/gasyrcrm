from django.urls import path
from . import views

app_name = 'appointments'

urlpatterns = [
    path('', views.list_appointments, name='list_appointments'),
    path('book/<int:appointment_id>/', views.book_appointment, name='book_appointment'),
]