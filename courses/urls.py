from django.urls import path, re_path
from .views import (
    CourseListView, CourseDetailView, LessonCreateView,
    ModuleDetailView, LessonDetailView,
    CreateCourseStep1View, CreateCourseStep2View, CreateOrEditTestView, ModuleCreateView, AddStudentsView,
    add_student_to_course, TakeTestView, test_result_view, search_students, EditCourseView, CourseDelete,
    delete_literature, CourseFinalTestView, SuccessVideoLinkEditView, bulk_create_lessons, CourseModulesView,
    ModuleCreateViewAPI, LessonCreateViewAPI, LiteratureCreateViewAPI, LiteratureDeleteViewAPI, CreateCourseStep3View,
    CreateCourseStep4View, CreateCourseStep5View, CreateCourseEndingView, student_results_view, publishCourse,
    student_test_results_view
)
from core.views import CoursePageView, CourseStudentLecturePageView, course_redirect, CourseStudentTestPageView
from django.conf import settings
from django.conf.urls.static import static
app_name = 'courses'

urlpatterns = [
    path('', CourseListView.as_view(), name='course_list'),
    path('<int:pk>/', CoursePageView.as_view(), name='course_detail'),
    path('student/<int:pk>/', course_redirect, name='course_start'),
    path('student/<int:pk>/<int:module_id>/<int:lesson_id>/lecture', CourseStudentLecturePageView.as_view(), name='course_student_lecture'),
    path('student/<int:pk>/<int:module_id>/<int:lesson_id>/test', CourseStudentTestPageView.as_view(), name='course_student_test_lesson'),
    path('student/<int:pk>/<int:module_id>/test', CourseStudentTestPageView.as_view(), name='course_student_test_module'),
    path('student/<int:pk>/test', CourseStudentTestPageView.as_view(), name='course_student_test_course'),
    path('edit/<int:pk>/', CourseDetailView.as_view(), name='course_detail_edit'),
    path('publish/<int:pk>/', publishCourse, name='course_publish'),
    path('edit/<int:pk>/about/', EditCourseView.as_view(), name='course_detail_edit_about'),
    path('delete/<int:pk>/', CourseDelete.as_view(), name='course_delete'),
    path('create/step1/', CreateCourseStep1View.as_view(), name='create_course_step1'),
    path('create/step2/', CreateCourseStep2View.as_view(), name='create_course_step2'),
    path('create/step3/<int:course_id>', CreateCourseStep3View.as_view(), name='create_course_step3'),
    path('create/step4/<int:course_id>', CreateCourseStep4View.as_view(), name='create_course_step4'),
    path('create/step5/<int:course_id>', CreateCourseStep5View.as_view(), name='create_course_step5'),
    path('create/ending/<int:course_id>', CreateCourseEndingView.as_view(), name='create_course_ending'),
    path('<int:course_id>/module/create/', ModuleCreateViewAPI.as_view(), name='module_create'),
    path('<int:module_id>/lesson/create/', LessonCreateViewAPI.as_view(), name='lesson_create'),
    path('<int:lesson_id>/literature/create/', LiteratureCreateViewAPI.as_view(), name='literature_create'),
    path('literature/<int:literature_id>/delete/', LiteratureDeleteViewAPI.as_view(), name='literature_delete'),
    path('module/<int:pk>/', ModuleDetailView.as_view(), name='module_detail'),
    path('<int:pk>/final_test/edit', CourseFinalTestView.as_view(), name='final_test_creation'),
    path('<int:pk>/success_video/edit', SuccessVideoLinkEditView.as_view(), name='success_video_edit'),
    path('lesson/<int:pk>/', LessonDetailView.as_view(), name='lesson_detail'),
    path('<str:parent_type>/<int:parent_id>/test/', CreateOrEditTestView.as_view(), name='create_edit_test'),
    path('course/<int:pk>/add-students/', AddStudentsView.as_view(), name='add_students'),
    path('<int:course_id>/add-student/<int:student_id>/', add_student_to_course, name='add_student_to_course'),
    path('course/search-students/', search_students, name='search_students'),
    path('literature/delete/', delete_literature, name='literature_delete'),

    path('<int:course_id>/student/<str:student_login_code>', student_results_view, name='student_results'),
    path('<int:course_id>/student/<str:student_login_code>/<int:submission_id>', student_test_results_view, name='student_test_results'),

    path('test/take/<int:course_id>/<int:module_id>/<int:lesson_id>/<int:test_id>/', TakeTestView.as_view(), name='take_test_lesson'),
    path('test/take/<int:course_id>/<int:module_id>/<int:test_id>/', TakeTestView.as_view(), name='take_test_module'),
    path('test/take/<int:course_id>/<int:test_id>/', TakeTestView.as_view(), name='take_test_course'),
    re_path(r'^test/result/(?P<score>\d+\.\d+)/$', test_result_view, name='test_result'),

    path('course/<int:course_id>/module/', ModuleDetailView.as_view(), name='module_detail'),
    path('module/<int:module_id>/bulk-create-lessons/', bulk_create_lessons, name='bulk_create_lessons'),
    path('module/<int:module_id>/update-module-and-lessons/', bulk_create_lessons, name='update_module_and_lessons'),
    path('<int:course_id>/modules/api/', CourseModulesView.as_view(), name='course-modules'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
