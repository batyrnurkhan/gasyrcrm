from django.urls import path
from . import views
from .views import AppointmentListCreateAPIView, AppointmentSetLinkAPIView, \
    appointments_for_day_api, AppointmentBookAPIView, cancel_appointment, success_appointment_view

app_name = "appointments"

urlpatterns = [
    path('', views.week_view, name='week_view'),
    path('api/appointments/<str:type>/<int:year>/<int:month>/<int:day>/', appointments_for_day_api, name='appointments_for_day_api'),
    path('api/appointments/', AppointmentListCreateAPIView.as_view(), name='appointment-list-create'),
    path('api/appointments/<int:pk>/set-link/', AppointmentSetLinkAPIView.as_view(), name='appointment-set-link'),
    path('api/appointments/<int:pk>/book/', AppointmentBookAPIView.as_view(), name='appointment-book'),
    path('success-appointment/', success_appointment_view, name='success-appointment'),
    path('appointments/cancel/<int:appointment_id>/', cancel_appointment, name='cancel_appointment'),

]