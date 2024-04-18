from django.urls import path, re_path
from .views import (
    CourseListView, CourseDetailView, LessonCreateView,
    ModuleDetailView, LessonDetailView,
    CreateCourseStep1View, CreateCourseStep2View, CreateOrEditTestView, ModuleCreateView, AddStudentsView,
    add_student_to_course, TakeTestView, test_result_view,
)
from core.views import CoursePageView

app_name = 'courses'

urlpatterns = [
    path('', CourseListView.as_view(), name='course_list'),
    path('<int:pk>/', CoursePageView.as_view(), name='course_detail'),
    path('edit/<int:pk>/', CourseDetailView.as_view(), name='course_detail_edit'),
    path('create/step1/', CreateCourseStep1View.as_view(), name='create_course_step1'),
    path('create/step2/', CreateCourseStep2View.as_view(), name='create_course_step2'),
    path('<int:course_id>/module/create/', ModuleCreateView.as_view(), name='module_create'),
    path('<int:module_id>/lesson/create/', LessonCreateView.as_view(), name='lesson_create'),
    path('module/<int:pk>/', ModuleDetailView.as_view(), name='module_detail'),
    path('lesson/<int:pk>/', LessonDetailView.as_view(), name='lesson_detail'),
    #path('test/<int:pk>/', TestDetailView.as_view(), name='test_detail'),
    path('<str:parent_type>/<int:parent_id>/test/', CreateOrEditTestView.as_view(), name='create_edit_test'),
    # path('<parent_type>/<int:parent_id>/test/create/', CreateTestView.as_view(), name='create_test'),
    # path('<parent_type>/<int:parent_id>/test/edit/<int:test_id>/', EditTestView.as_view(), name='edit_test'),
    path('course/<int:pk>/add-students/', AddStudentsView.as_view(), name='add_students'),
    path('<int:course_id>/add-student/<int:student_id>/', add_student_to_course, name='add_student_to_course'),

    path('test/take/<int:test_id>/', TakeTestView.as_view(), name='take_test'),
    re_path(r'^test/result/(?P<score>\d+\.\d+)/$', test_result_view, name='test_result'),
]