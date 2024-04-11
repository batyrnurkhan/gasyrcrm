from django.urls import path
from .views import CourseListView, CourseDetailView, ModuleCreateView, LessonCreateView, ModuleDetailView, \
    create_course_step1, create_course_step2

app_name = 'courses'

urlpatterns = [
    path('list/', CourseListView.as_view(), name='list'),
    path('<int:pk>/', CourseDetailView.as_view(), name='course_detail'),
    path('create/step1/', create_course_step1, name='create_course_step1'),
    path('create/step2/', create_course_step2, name='create_course_step2'),
    path('<int:course_id>/module/create/', ModuleCreateView.as_view(), name='module_create'),
    path('<int:module_id>/lesson/create/', LessonCreateView.as_view(), name='lesson_create'),
    path('module/<int:pk>/', ModuleDetailView.as_view(), name='module_detail'),
    path('module/<int:module_id>/lesson/create/', LessonCreateView.as_view(), name='lesson_create'),
]