from django.urls import path
from .views import SubjectListView, group_template_list, LessonCreateView, LessonDetailView, search_students

app_name = 'subjects'

urlpatterns = [
    path('', SubjectListView.as_view(), name='subject-list'),
    path('grouptemplates/', group_template_list, name='grouptemplate-list'),
    path('lessons-create/<int:time_id>/', LessonCreateView.as_view(), name='lesson-create'),
    path('lessons/<int:pk>/', LessonDetailView.as_view(), name='lesson-detail'),
    path('search/', search_students, name='search-students'),  # Corrected URL name
]
