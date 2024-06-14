from django.urls import path
from .views import SubjectListView, group_template_list, LessonCreateView, LessonDetailView, search_students, \
    create_volunteer_channel, set_grade, LessonListView, grades_by_day_view, home_view, \
    tasks_view, weekly_schedule_view, psy_appointment_view, group_templates_view, EditGroupTemplateView, search_users, \
    mini_schedule_view, update_google_meet_link, student_tasks_view, upload_task_view, download_task_file, \
    download_submission_file, download_grade_file, create_achievement, achievements_list, task_submissions_view, \
    ori_appointment_view

app_name = 'subjects'

urlpatterns = [
    path('home/', home_view, name='home'),
    path('tasks/', tasks_view, name='tasks'),
    path('weekly-schedule/', weekly_schedule_view, name='weekly-schedule'),
    path('mini-schedule/', mini_schedule_view, name='mini-schedule'),
    path('psy-appointment/', psy_appointment_view, name='psy-appointment'),
    path('ori-appointment/', ori_appointment_view, name='ori-appointment'),


    path('subject-list/', SubjectListView.as_view(), name='subject-list'),
    path('grouptemplate-create/', group_template_list, name='grouptemplate-list'),
    path('group-templates/', group_templates_view, name='group_templates_view'),
    path('edit-group-template/<int:pk>/', EditGroupTemplateView.as_view(), name='edit_template_url'),

    path('lessons/', LessonListView.as_view(), name='lesson-list'),
    path('lessons-create/<int:time_id>/', LessonCreateView.as_view(), name='lesson-create'),

    path('set-achievement/', create_achievement, name='set_achievement'),
    path('achievements/', achievements_list, name='achievements_list'),

    path('lessons/<int:pk>/', LessonDetailView.as_view(), name='lesson-detail'),

    path('search/', search_students, name='search-students'),

    # path('volunteer_channels/create/', create_volunteer_channel, name='create_volunteer_channel'),
    path('volunteer_channels/', create_volunteer_channel, name='volunteer_channel_list'),
    path('set-grade/<int:lesson_id>/', set_grade, name='set_grade'),
    path('grades-by-day/', grades_by_day_view, name='grades-by-day'),

    path('search-users/', search_users, name='search-users'),
    path('api/lesson/<int:lesson_id>/update_google_meet_link/', update_google_meet_link, name='update_google_meet_link'),
    path('tasks/<int:task_id>/submissions/', task_submissions_view, name='task_submissions_view'),

    path('tasks-student/', student_tasks_view, name='student_tasks_view'),
    path('api/upload_task/', upload_task_view, name='upload_task_view'),
    path('download_task_file/<int:task_id>/', download_task_file, name='download_task_file'),
    path('download-grade-file/<int:grade_id>/', download_grade_file, name='download_grade_file'),
    path('download_submission_file/<int:submission_id>/', download_submission_file, name='download_submission_file'),
]
