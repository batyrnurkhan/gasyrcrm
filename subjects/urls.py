from django.urls import path
from .views import SubjectListView, group_template_list, LessonListView, LessonDetailView, search_students

app_name = 'subjects'

urlpatterns = [
    path('', SubjectListView.as_view(), name='subject-list'),
    path('grouptemplates/', group_template_list, name='grouptemplate-list'),
    path('lessons-create/', LessonListView.as_view(), name='lesson-list'),
    path('lessons/<int:pk>/', LessonDetailView.as_view(), name='lesson-detail'),
    path('search/', search_students, name='search-students'),  # Corrected URL name
]
