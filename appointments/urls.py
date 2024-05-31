from django.urls import path
from . import views
from .views import AppointmentListCreateAPIView, AppointmentSetLinkAPIView, set_link_view, create_appointment_view, \
    appointments_for_day



urlpatterns = [
    path('', views.week_view, name='week_view'),
    path('create-appointment/', create_appointment_view, name='create-appointment'),
    path('appointments/<int:year>/<int:month>/<int:day>/', appointments_for_day, name='appointments_for_day'),
    path('set-link/', set_link_view, name='set-link'),
    path('appointments/<int:year>/<int:month>/<int:day>/', views.appointments_for_day, name='appointments_for_day'),
    path('api/appointments/', AppointmentListCreateAPIView.as_view(), name='appointment-list-create'),
    path('api/appointments/<int:pk>/set-link/', AppointmentSetLinkAPIView.as_view(), name='appointment-set-link'),
]