from django.urls import path
from .views import SubjectListView, group_template_list, LessonCreateView, LessonDetailView, search_students, \
    create_volunteer_channel, volunteer_channel_list

app_name = 'subjects'

urlpatterns = [
    path('', SubjectListView.as_view(), name='subject-list'),
    path('grouptemplates/', group_template_list, name='grouptemplate-list'),
    path('lessons-create/<int:time_id>/', LessonCreateView.as_view(), name='lesson-create'),
    path('lessons/<int:pk>/', LessonDetailView.as_view(), name='lesson-detail'),
    path('search/', search_students, name='search-students'),
    path('volunteer_channels/create/', create_volunteer_channel, name='create_volunteer_channel'),
    path('volunteer_channels/', volunteer_channel_list, name='volunteer_channel_list'),
]
