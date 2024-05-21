from django.urls import path
from .views import SubjectListView, group_template_list, LessonCreateView, LessonDetailView, search_students, \
    create_volunteer_channel, volunteer_channel_list, set_grade, LessonListView, grades_by_day_view, home_view, \
    tasks_view, LessonsByWeekdayView

app_name = 'subjects'

urlpatterns = [
    path('home/', home_view, name='home'),  # Add this line
    path('tasks/', tasks_view, name='tasks'),
    path('weekly-schedule/', LessonsByWeekdayView.as_view(), name='weekly-schedule'),  # Add this line
    path('subject-list/', SubjectListView.as_view(), name='subject-list'),

    path('lessons/', LessonListView.as_view(), name='lesson-list'),
    path('grouptemplates/', group_template_list, name='grouptemplate-list'),
    path('lessons-create/<int:time_id>/', LessonCreateView.as_view(), name='lesson-create'),
    path('lessons/<int:pk>/', LessonDetailView.as_view(), name='lesson-detail'),
    path('search/', search_students, name='search-students'),
    path('volunteer_channels/create/', create_volunteer_channel, name='create_volunteer_channel'),
    path('volunteer_channels/', volunteer_channel_list, name='volunteer_channel_list'),
    path('set-grade/<int:lesson_id>/', set_grade, name='set_grade'),
    path('grades-by-day/', grades_by_day_view, name='grades-by-day'),  # Add this line

]
