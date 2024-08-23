from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import redirect, get_object_or_404
from django.views.generic import TemplateView, DetailView
from django.urls import reverse_lazy, reverse
from django.db.models import Prefetch, Q

from courses.models import Course, Module, Lesson, TestSubmission, Test
from django.http import JsonResponse
from datetime import date, timedelta
from django.utils.translation import activate
from django.utils.formats import date_format

#locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')

def get_next_step(course, current_lesson=None, current_module=None):
    if current_lesson:
        module = current_lesson.module

        # Check if there's a homework next
        next_homework = current_lesson.homeworks.first()
        if next_homework:
            return reverse('courses:course_student_homework', kwargs={
                'course_id': course.id,
                'module_id': module.id,
                'pk': next_homework.id
            })

        # Check if there's literature next
        next_literature = current_lesson.literatures.first()
        if next_literature:
            return reverse('courses:course_student_literature', kwargs={
                'course_id': course.id,
                'module_id': module.id,
                'lesson_id': current_lesson.id
            })

        # Check if there's a test next
        next_test = current_lesson.tests.first()
        if next_test:
            return reverse('courses:course_student_test_lesson', kwargs={
                'pk': course.id,
                'module_id': module.id,
                'lesson_id': current_lesson.id
            })

        # Move to the next lesson in the module if available
        next_lesson = module.lessons.filter(id__gt=current_lesson.id).first()
        if next_lesson:
            return reverse('courses:course_student_lecture', kwargs={
                'pk': course.id,
                'module_id': module.id,
                'lesson_id': next_lesson.id
            })

    # If current_module is provided, handle module-level navigation
    if current_module:
        # Check if there's a module test next
        next_module_test = current_module.tests.first()
        if next_module_test:
            return reverse('courses:course_student_test_module', kwargs={
                'pk': course.id,
                'module_id': current_module.id
            })

        # Move to the next module if available
        next_module = course.modules.filter(id__gt=current_module.id).first()
        if next_module:
            next_lesson = next_module.lessons.first()
            if next_lesson:
                return reverse('courses:course_student_lecture', kwargs={
                    'pk': course.id,
                    'module_id': next_module.id,
                    'lesson_id': next_lesson.id
                })

    # If it's the last module, move to the course test
    next_course_test = course.tests.first()
    if next_course_test:
        return reverse('courses:course_student_test_course', kwargs={'pk': course.id})

    # If it's the last course step, go to the course final page
    return reverse('courses:course_final', kwargs={'course_id': course.id})


def get_week_dates(request):
    # Activate Russian locale
    activate('ru-RU')

    week_offset = int(request.GET.get('week_offset', 0))
    today = date.today()
    start_of_week = today - timedelta(days=today.weekday()) + timedelta(weeks=week_offset)
    end_of_week = start_of_week + timedelta(days=6)

    # Use Django's date formatting utility which respects localization
    month_name = date_format(end_of_week, format='F')

    response_data = {
        'start_day': start_of_week.day,
        'end_day': end_of_week.day,
        'month_name': month_name,  # This will now be in Russian
        'dates_of_week': [(start_of_week + timedelta(days=i)).isoformat() for i in range(7)]
    }

    return JsonResponse(response_data)


class HomePageView(LoginRequiredMixin, TemplateView):

    def get_template_names(self):
        if self.request.user.role == "Teacher":
            return "core/teacher-home.html"
        else:
            return "core/student-home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        if user.role == "Teacher":
            courses = Course.objects.filter(created_by=user)
            context["published_courses"] = courses.filter(published=True)
            context["unpublished_courses"] = courses.filter(published=False)
        else:
            context["courses"] = Course.objects.filter(published=True).all()

        # Get last opened content information
        last_opened_content_id = user.last_opened_content_id
        course_name = None
        test_completion_percentage = 0

        if last_opened_content_id:
            # Check if the content is a course
            course = Course.objects.filter(id=last_opened_content_id).first()
            if course:
                course_name = course.course_name
            else:
                # Check if the content is a module
                module = Module.objects.filter(id=last_opened_content_id).first()
                if module:
                    course = module.course
                    course_name = course.course_name
                else:
                    # Check if the content is a lesson
                    lesson = Lesson.objects.filter(id=last_opened_content_id).first()
                    if lesson:
                        course = lesson.module.course
                        course_name = course.course_name

            # Calculate test completion percentage for the course
            if course:
                total_tests = Test.objects.filter(
                    Q(content_type=ContentType.objects.get_for_model(Course), object_id=course.id) |
                    Q(content_type=ContentType.objects.get_for_model(Module), object_id__in=course.modules.all()) |
                    Q(content_type=ContentType.objects.get_for_model(Lesson), object_id__in=Lesson.objects.filter(module__course=course))
                ).count()
                completed_tests = TestSubmission.objects.filter(user=user, test__in=Test.objects.filter(
                    Q(content_type=ContentType.objects.get_for_model(Course), object_id=course.id) |
                    Q(content_type=ContentType.objects.get_for_model(Module), object_id__in=course.modules.all()) |
                    Q(content_type=ContentType.objects.get_for_model(Lesson), object_id__in=Lesson.objects.filter(module__course=course))
                ), score__gte=50).count()

                if total_tests > 0:
                    test_completion_percentage = min((completed_tests / total_tests) * 100, 100)

        context['last_opened_content_id'] = last_opened_content_id
        context['course_name'] = course_name
        context['test_completion_percentage'] = test_completion_percentage

        return context




class MyCoursesPageView(LoginRequiredMixin, TemplateView):
    template_name = 'core/my-courses.html'

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        # Add in a QuerySet of all the books
        context["courses"] = Course.objects.filter(users__phone_number__contains=self.request.user.phone_number)
        return context


class CompletedCoursesPageView(LoginRequiredMixin, TemplateView):
    template_name = 'core/completed-courses.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        completed_courses = []

        courses = user.courses.all()
        for course in courses:
            if course.calculate_completion_percentage(user) >= 100:
                completed_courses.append(course)

        context['completed_courses'] = completed_courses

        return context


class CoursePageView(LoginRequiredMixin, DetailView):
    model = Course
    template_name = 'core/course_detail.html'

    def dispatch(self, request, *args, **kwargs):
        course = Course.objects.filter(pk=self.kwargs['pk'])
        if not course.exists() or not course.first().published:
            messages.error(request, "Курса не существует")
            return redirect(reverse("home"))

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        modules = Module.objects.filter(course_id=self.object.id).prefetch_related(Prefetch('tests'))

        accessible_modules = []
        lessons_count = 0
        allow_access_to_next = True

        for i, module in enumerate(modules):
            if i == 0:  # The first module is always accessible
                accessible_modules.append(module)
                lessons_count += Lesson.objects.filter(module=module).count()
                continue

            # Check if the previous module's test was passed
            previous_module = accessible_modules[-1]
            test = previous_module.tests.first()  # Assuming only one test per module
            if test:
                test_submission = TestSubmission.objects.filter(user=user, test=test).first()
                if test_submission and test_submission.score >= 50:
                    accessible_modules.append(module)
                    lessons_count += Lesson.objects.filter(module=module).count()
                else:
                    break  # Stop adding modules if the previous one wasn't passed
            else:
                accessible_modules.append(module)
                lessons_count += Lesson.objects.filter(module=module).count()

        context.update({
            'modules': accessible_modules,  # Only modules the user can access
            'modules_count': len(accessible_modules),
            'lessons_count': lessons_count,
            'courses': Course.objects.exclude(id=self.object.id)[:2]  # Suggesting other courses
        })

        return context


def course_redirect(request, pk):
    try:
        module = Module.objects.filter(course_id=pk).first()
        if not module:
            messages.error(request, "Учитель не загрузил модули")
            return redirect(reverse("home"))

        lesson = Lesson.objects.filter(module_id=module.pk).first()
        if not lesson:
            messages.error(request, "Учитель не загрузил уроки")
            return redirect(reverse("home"))

    except Exception as e:
        messages.error(request, f"Error occurred: {str(e)}")
        return redirect(reverse("home"))

    return redirect(
        reverse("courses:course_student_lecture", kwargs={'pk': pk, 'module_id': module.id, 'lesson_id': lesson.id}))

class CourseStudentLecturePageView(LoginRequiredMixin, DetailView):
    model = Course
    template_name = 'core/student/course_lecture.html'

    def dispatch(self, request, *args, **kwargs):
        course = Course.objects.filter(pk=self.kwargs['pk']).first()
        if not course or not course.published:
            messages.error(request, "Курса не существует")
            return redirect(reverse("home"))
        if request.user not in course.users.all():
            messages.error(request, "Вас нет в этом курсе")
            return redirect(reverse("home"))
        if request.user.role == 'Student':
            lesson = Lesson.objects.filter(pk=self.kwargs['lesson_id']).first()
            request.user.last_opened_content_id = lesson.id
            request.user.save()
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course = self.get_object()
        user = self.request.user
        current_lesson = get_object_or_404(Lesson, pk=self.kwargs['lesson_id'])
        next_step_url = get_next_step(course, current_lesson=current_lesson)

        context.update({
            'lesson': current_lesson,
            'module': current_lesson.module,
            'next_step_url': next_step_url
        })

        lesson = Lesson.objects.filter(pk=self.kwargs['lesson_id']).first()
        module = Module.objects.filter(lessons=lesson).first()
        if lesson and module:
            context['lesson'] = lesson
            context['module'] = module
            for i, item in enumerate(module.lessons.all()):
                if item == lesson:
                    context['lesson_position'] = i + 1
                    break

        modules = course.modules.prefetch_related(
            Prefetch('lessons', queryset=Lesson.objects.prefetch_related('tests'))
        )
        accessible_modules = []
        blocked_modules = []

        previous_module_passed = True

        for module in modules:
            module_tests = module.tests.all()
            lesson_tests = Test.objects.filter(
                content_type=ContentType.objects.get_for_model(Lesson),
                object_id__in=module.lessons.values_list('id', flat=True)
            )
            all_tests = (module_tests | lesson_tests).distinct()

            if all_tests.exists():
                passed_tests = all_tests.filter(test_submissions__user=user, test_submissions__score__gte=50).distinct()
                user_passed_all_tests = passed_tests.count() == all_tests.count()
            else:
                user_passed_all_tests = True

            if previous_module_passed:
                module.accessible = True
                accessible_modules.append(module)
            else:
                module.accessible = False
                blocked_modules.append(module)

            previous_module_passed = user_passed_all_tests

        context['modules'] = accessible_modules + blocked_modules  # Show all modules
        return context


# class CourseStudentTestPageView(LoginRequiredMixin, DetailView):
#     model = Course
#     template_name = 'core/student/course_lesson_test.html'
#
#     def get_template_names(self):
#         user = self.request.user
#         if self.kwargs['lesson_id']:
#             lessons = Lesson.objects.filter(pk=self.kwargs['lesson_id'])
#             if lessons.exists():
#                 if lessons.first().tests:
#                     test = lessons.first().tests.first()
#                     submission = TestSubmission.objects.filter(user=user, test=test)
#                     if submission.exists():
#                         return "core/student/course_lesson_test_results.html"
#                     return "core/student/course_lesson_test.html"
#                 return "core/student/course_lesson_test.html"
#
#         elif self.kwargs['module_id']:
#             test = Module.objects.filter(pk=self.kwargs['module_id']).first().tests.first()
#             submission = TestSubmission.objects.filter(user=user, test=test)
#             if submission.exists():
#                 return "core/student/course_module_test_results.html"
#             return "core/student/course_module_test.html"
#         else:
#             test = Course.objects.filter(pk=self.kwargs['pk']).first().tests.first()
#             submission = TestSubmission.objects.filter(user=user, test=test)
#             if submission.exists():
#                 return "core/student/course_test_results.html"
#             return "core/student/course_test.html"
#
#     def dispatch(self, request, *args, **kwargs):
#         course = Course.objects.filter(pk=self.kwargs['pk'])
#         if not course.exists() or not course.first().published:
#             messages.error(request, "Курса не существует")
#             return redirect(reverse("home"))
#         if self.request.user not in course.first().users.all():
#             messages.error(request, "Вас нет в этом курсе")
#             return redirect(reverse("home"))
#         if not self.kwargs.get('lesson_id', None): self.kwargs['lesson_id'] = None
#         if not self.kwargs.get('module_id', None): self.kwargs['module_id'] = None
#         return super().dispatch(request, *args, **kwargs)
#
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         course = self.get_object()
#         if self.kwargs['lesson_id']:
#             lesson = Lesson.objects.filter(pk=self.kwargs['lesson_id'])
#             module = Module.objects.filter(pk=self.kwargs['module_id'])
#             context['lesson'] = lesson.first()
#             test = lesson.first().tests.first()
#             for i, item in enumerate(module.first().lessons.all()):
#                 if item == lesson.first():
#                     context['lesson_position'] = i+1
#                     break
#             context['module'] = module.first()
#             context['module_name'] = module.first().module_name
#         elif self.kwargs['module_id']:
#             module = Module.objects.filter(pk=self.kwargs['module_id'])
#             test = module.first().tests.first()
#             context['module'] = module.first()
#             context['module_name'] = module.first().module_name
#         else:
#             course = Course.objects.filter(pk=self.kwargs['pk'])
#             test = course.first().tests.first()
#         user = self.request.user
#         submission = TestSubmission.objects.filter(user=user, test=test)
#         if submission.exists():
#             if not self.kwargs['lesson_id'] and not self.kwargs['module_id']:
#                 modules = Module.objects.filter(course_id=self.object.id).prefetch_related(Prefetch('tests'))
#                 lessons_count = 0
#
#                 for module in enumerate(modules):
#                     lessons_count += Lesson.objects.filter(module=module).count()
#                 context['modules_count'] = len(modules)
#                 context['lessons_count'] = lessons_count
#             context['submission'] = submission.first()
#
#         modules = course.modules.prefetch_related(
#             Prefetch('lessons', queryset=Lesson.objects.prefetch_related('tests'))
#         )
#         accessible_modules = []
#         blocked_modules = []
#
#         previous_module_passed = True
#
#         for module in modules:
#             module_tests = module.tests.all()
#             lesson_tests = Test.objects.filter(
#                 content_type=ContentType.objects.get_for_model(Lesson),
#                 object_id__in=module.lessons.values_list('id', flat=True)
#             )
#             all_tests = (module_tests | lesson_tests).distinct()
#
#             if all_tests.exists():
#                 passed_tests = all_tests.filter(test_submissions__user=user, test_submissions__score__gte=50).distinct()
#                 user_passed_all_tests = passed_tests.count() == all_tests.count()
#             else:
#                 user_passed_all_tests = True
#
#             if previous_module_passed:
#                 module.accessible = True
#                 accessible_modules.append(module)
#             else:
#                 module.accessible = False
#                 blocked_modules.append(module)
#
#             previous_module_passed = user_passed_all_tests
#
#         print("Accessible Modules:", [m.module_name for m in accessible_modules])
#         print("Blocked Modules:", [m.module_name for m in blocked_modules])
#
#         context['modules'] = accessible_modules
#         context['blocked_modules'] = blocked_modules
#         return context
class CourseStudentTestPageView(LoginRequiredMixin, DetailView):
    model = Course
    template_name = 'core/student/course_lesson_test.html'

    def get_template_names(self):
        user = self.request.user
        lesson_id = self.kwargs.get('lesson_id')
        module_id = self.kwargs.get('module_id')

        if lesson_id:
            lessons = Lesson.objects.filter(pk=lesson_id)
            if lessons.exists():
                lesson = lessons.first()
                test = lesson.tests.first()
                submission = TestSubmission.objects.filter(user=user, test=test)
                if submission.exists():
                    return "core/student/course_lesson_test_results.html"
                return "core/student/course_lesson_test.html"

        elif module_id:
            module = Module.objects.filter(pk=module_id).first()
            if module:
                test = module.tests.first()
                submission = TestSubmission.objects.filter(user=user, test=test)
                if submission.exists():
                    return "core/student/course_module_test_results.html"
                return "core/student/course_module_test.html"
        else:
            course = Course.objects.filter(pk=self.kwargs['pk']).first()
            if course:
                test = course.tests.first()
                if test:
                    submission = TestSubmission.objects.filter(user=user, test=test)
                    if submission.exists():
                        return "core/student/course_test_results.html"
                    return "core/student/course_test.html"
                else:
                    return "core/student/course_test_results.html"

        return self.template_name

    def dispatch(self, request, *args, **kwargs):
        course = Course.objects.filter(pk=self.kwargs['pk']).first()
        if not course or not course.published:
            messages.error(request, "Курса не существует")
            return redirect(reverse("home"))
        if self.request.user not in course.users.all():
            messages.error(request, "Вас нет в этом курсе")
            return redirect(reverse("home"))
        if not self.kwargs.get('lesson_id', None): self.kwargs['lesson_id'] = None
        if not self.kwargs.get('module_id', None): self.kwargs['module_id'] = None

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course = self.get_object()
        lesson_id = self.kwargs.get('lesson_id')
        module_id = self.kwargs.get('module_id')

        if lesson_id:
            lesson = Lesson.objects.filter(pk=lesson_id).first()
            module = Module.objects.filter(pk=module_id).first()
            if lesson and module:
                context['lesson'] = lesson
                test = lesson.tests.first()
                for i, item in enumerate(module.lessons.all()):
                    if item == lesson:
                        context['lesson_position'] = i + 1
                        break
                context['module'] = module
                context['module_name'] = module.module_name

        elif module_id:
            module = Module.objects.filter(pk=module_id).first()
            if module:
                test = module.tests.first()
                context['module'] = module
                context['module_name'] = module.module_name

        else:
            course = Course.objects.filter(pk=self.kwargs['pk']).first()
            if course:
                test = course.tests.first()

        user = self.request.user
        submission = TestSubmission.objects.filter(user=user, test=test)
        if submission.exists():
            if not lesson_id and not module_id:
                modules = Module.objects.filter(course_id=course.id).prefetch_related(Prefetch('tests'))
                lessons_count = 0

                for module in modules:
                    lessons_count += module.lessons.count()
                context['modules_count'] = modules.count()
                context['lessons_count'] = lessons_count
            context['submission'] = submission.first()

        # Calculate if all module and lesson tests are passed
        module_tests = Test.objects.filter(object_id__in=course.modules.values_list('id', flat=True),
                                           content_type=ContentType.objects.get_for_model(Module))
        lesson_tests = Test.objects.filter(
            object_id__in=Lesson.objects.filter(module__course=course).values_list('id', flat=True),
            content_type=ContentType.objects.get_for_model(Lesson))

        all_tests = list(module_tests) + list(lesson_tests)
        passed_tests = TestSubmission.objects.filter(user=user, test__in=all_tests, score__gte=50).values_list('test', flat=True).distinct()

        # Grant access to the course test if all module and lesson tests are passed
        all_tests_passed = all(test.id in passed_tests for test in all_tests)

        if all_tests_passed:
            context['course_test_accessible'] = True
        else:
            context['course_test_accessible'] = False

        modules = course.modules.prefetch_related(
            Prefetch('lessons', queryset=Lesson.objects.prefetch_related('tests'))
        )
        accessible_modules = []
        blocked_modules = []

        previous_module_passed = True

        for module in modules:
            module_tests = module.tests.all()
            lesson_tests = Test.objects.filter(
                content_type=ContentType.objects.get_for_model(Lesson),
                object_id__in=module.lessons.values_list('id', flat=True)
            )
            all_tests = (module_tests | lesson_tests).distinct()

            if all_tests.exists():
                passed_tests = all_tests.filter(test_submissions__user=user, test_submissions__score__gte=50).distinct()
                user_passed_all_tests = passed_tests.count() == all_tests.count()
            else:
                user_passed_all_tests = True

            if previous_module_passed:
                module.accessible = True
                accessible_modules.append(module)
            else:
                module.accessible = False
                blocked_modules.append(module)

            previous_module_passed = user_passed_all_tests

        context['modules'] = accessible_modules + blocked_modules  # Show all modules
        context['all_tests_passed'] = all_tests_passed
        return context

class WelcomePageView(TemplateView):
    template_name = 'core/welcome.html'
