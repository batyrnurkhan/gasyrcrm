from django.urls import path
from .views import shifts_view

app_name = "schedule"

urlpatterns = [
    path('shifts/', shifts_view, name='shifts'),
]
