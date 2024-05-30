from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import psychologist_home, appointment_view, set_meeting_link, AppointmentViewSet, view1, view2

# API router
router = DefaultRouter()
router.register(r'appointments', AppointmentViewSet, basename='appointment')

urlpatterns = [
    path('home/', psychologist_home, name='psychologist_home'),
    path('add_appointment/', appointment_view, name='add_appointment'),
    path('set_meeting_link/', set_meeting_link, name='set_meeting_link'),
    path('api/', include(router.urls)),  # Include the API router
    path('psychologist/', view1.as_view(), name='psychologist_home_page'),
    path('student/', view2.as_view(), name='student_home_page'),
]