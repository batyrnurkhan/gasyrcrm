from django.urls import path
from . import views
from .views import psychologist_home, appointment_view, set_meeting_link

app_name = 'appointments'

urlpatterns = [
    path('home/', psychologist_home, name='psychologist_home'),
    path('add_appointment/', appointment_view, name='add_appointment'),
    path('set_meeting_link/', set_meeting_link, name='set_meeting_link'),
]
