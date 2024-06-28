from django.urls import path
from .views import shifts_view, get_shifts_for_day

app_name = "schedule"

urlpatterns = [
    path('shifts/', shifts_view, name='shifts'),
    path('get-shifts/<str:day>/', get_shifts_for_day, name='get_shifts_for_day'),
]
