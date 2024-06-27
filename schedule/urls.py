from django.urls import path
from .views import shifts_view, lessons_by_day_view

app_name = "schedule"

urlpatterns = [
    path('shifts/', shifts_view, name='shifts'),
    path('lessons/<str:day>/', lessons_by_day_view, name='lessons-by-day'),

]
