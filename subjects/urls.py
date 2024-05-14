from django.urls import path
from .views import SubjectListView, GroupTemplateListView, LessonListView, LessonDetailView

app_name = 'subjects'

urlpatterns = [
    path('subjects/', SubjectListView.as_view(), name='subject-list'),
    path('grouptemplates/', GroupTemplateListView.as_view(), name='grouptemplate-list'),
    path('lessons/', LessonListView.as_view(), name='lesson-list'),
    path('lessons/<int:pk>/', LessonDetailView.as_view(), name='lesson-detail'),
]
