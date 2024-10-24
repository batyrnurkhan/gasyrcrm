from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import redirect, get_object_or_404
from django.views.generic import TemplateView, DetailView
from django.urls import reverse_lazy, reverse
from django.db.models import Prefetch, Q
from courses.models import Course, Module, Lesson, TestSubmission, Test, StudentHomework, Homework
from django.http import JsonResponse
from datetime import date, timedelta
from django.utils.translation import activate
from django.utils.formats import date_format

#locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')

def check_final_test_access(user, course):
    # Check if all module and lesson tests are passed
    module_tests = Test.objects.filter(
        object_id__in=course.modules.values_list('id', flat=True),
        content_type=ContentType.objects.get_for_model(course.modules.model)
    )

    lesson_tests = Test.objects.filter(
        object_id__in=Lesson.objects.filter(module__course=course).values_list('id', flat=True),
        content_type=ContentType.objects.get_for_model(Lesson)
    )

    all_tests = list(module_tests) + list(lesson_tests)
    passed_tests = TestSubmission.objects.filter(
        user=user, test__in=all_tests, score__gte=50
    ).values_list('test', flat=True).distinct()

    all_tests_passed = all(test.id in passed_tests for test in all_tests)

    # Check if all homework has been submitted
    homeworks = Homework.objects.filter(lesson__module__course=course)
    submitted_homeworks = StudentHomework.objects.filter(
        student=user,
        lesson__in=homeworks.values_list('lesson', flat=True)
    )

    all_homeworks_submitted = submitted_homeworks.count() == homeworks.count()

    # Return True if all tests and homework are completed
    return all_tests_passed and all_homeworks_submitted


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
        if self.request.user.role in ["Teacher", "Mentor"]:
            return "core/teacher-home.html"
        else:
            return "core/student-home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        if user.role in ["Teacher", "Mentor"]:
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
        next_step_url = self.get_next_step(current_lesson, course)
        # Add lesson and module details for the sidebar
        context['lesson'] = current_lesson
        context['module'] = current_lesson.module
        context['next_step_url'] = next_step_url

        # Sidebar: Retrieve accessible and blocked modules
        modules = course.modules.prefetch_related(
            Prefetch('lessons', queryset=Lesson.objects.prefetch_related('tests'))
        )
        accessible_modules, blocked_modules = self.get_accessible_modules(user, modules)

        # Check if final test (Финал) is accessible
        context['course_test_accessible'] = self.check_final_test_access(user, course)
        context['all_tests_passed'] = self.check_final_test_access(user, course)

        context['modules'] = accessible_modules + blocked_modules
        return context

    def get_next_step(self, lesson, course):
        """Redirect based on priority order: lesson test, literature, homework, module test, next module lesson."""

        # 1. Check if there's a test for the lesson
        next_test = lesson.tests.first()
        if next_test:
            return reverse('courses:course_student_test_lesson', kwargs={
                'pk': course.id,  # Use 'pk' here based on your error message
                'module_id': lesson.module.id,
                'lesson_id': lesson.id
            })

        # 2. If no test, check for literature
        next_literature = lesson.literatures.first()
        if next_literature:
            return reverse('courses:course_student_literature', kwargs={
                'course_id': course.id,
                'module_id': lesson.module.id,
                'lesson_id': lesson.id
            })

        # 3. If no literature, check for homework
        next_homework = lesson.homeworks.first()
        if next_homework:
            return reverse('courses:course_student_homework', kwargs={
                'course_id': course.id,
                'module_id': lesson.module.id,
                'pk': lesson.id  # Use 'pk' as per your homework URL pattern
            })

        # 4. If no homework, check for module test
        next_module_test = lesson.module.tests.first()
        if next_module_test:
            return reverse('courses:course_student_test_module', kwargs={
                'course_id': course.id,
                'module_id': lesson.module.id
            })

        # 5. If no module test, move to the next module’s first lesson
        next_module = course.modules.filter(id__gt=lesson.module.id).first()
        if next_module:
            next_lesson = next_module.lessons.first()
            if next_lesson:
                return reverse('courses:course_student_lecture', kwargs={
                    'course_id': course.id,
                    'module_id': next_module.id,
                    'lesson_id': next_lesson.id
                })

        # Fallback: No further steps, return to final course page

    def get_accessible_modules(self, user, modules):
        """Determine which modules are accessible based on test completion."""
        accessible_modules = []
        blocked_modules = []
        previous_module_passed = True

        for module in modules:
            # Check if all tests in the module and its lessons are passed
            module_tests = module.tests.all()
            lesson_tests = Test.objects.filter(
                content_type=ContentType.objects.get_for_model(Lesson),
                object_id__in=module.lessons.values_list('id', flat=True)
            )
            all_tests = (module_tests | lesson_tests).distinct()

            if all_tests.exists():
                passed_tests = all_tests.filter(
                    test_submissions__user=user, test_submissions__score__gte=50
                ).distinct()
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

        return accessible_modules, blocked_modules

    def check_final_test_access(self, user, course):
        """Check if the user has passed all tests and submitted all homework."""
        # Get all the course, module, and lesson tests
        module_tests = Test.objects.filter(
            object_id__in=course.modules.values_list('id', flat=True),
            content_type=ContentType.objects.get_for_model(Module)
        )
        lesson_tests = Test.objects.filter(
            object_id__in=Lesson.objects.filter(module__course=course).values_list('id', flat=True),
            content_type=ContentType.objects.get_for_model(Lesson)
        )
        all_tests = list(module_tests) + list(lesson_tests)

        # Get the user's passed tests (score >= 50%)
        passed_tests = TestSubmission.objects.filter(
            user=user, test__in=all_tests, score__gte=50
        ).values_list('test', flat=True).distinct()

        # Check if all tests are passed
        all_tests_passed = all(test.id in passed_tests for test in all_tests)

        # Get all homeworks and check if all are submitted
        homeworks = Homework.objects.filter(lesson__module__course=course)
        submitted_homeworks = StudentHomework.objects.filter(
            student=user, lesson__in=homeworks.values_list('lesson', flat=True)
        )
        all_homeworks_submitted = submitted_homeworks.count() == homeworks.count()

        # Grant access to the final test if all tests are passed and all homework is submitted
        return all_tests_passed and all_homeworks_submitted

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
        user = self.request.user

        # Handle lesson context
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

        # Handle module context
        elif module_id:
            module = Module.objects.filter(pk=module_id).first()
            if module:
                test = module.tests.first()
                context['module'] = module
                context['module_name'] = module.module_name

        # Handle course context
        else:
            course = Course.objects.filter(pk=self.kwargs['pk']).first()
            if course:
                test = course.tests.first()

        # Check if there is a test submission
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

        # Calculate total tests and passed tests
        module_tests = Test.objects.filter(object_id__in=course.modules.values_list('id', flat=True),
                                           content_type=ContentType.objects.get_for_model(Module))
        lesson_tests = Test.objects.filter(
            object_id__in=Lesson.objects.filter(module__course=course).values_list('id', flat=True),
            content_type=ContentType.objects.get_for_model(Lesson))

        all_tests = list(module_tests) + list(lesson_tests)
        passed_tests = TestSubmission.objects.filter(user=user, test__in=all_tests, score__gte=50).values_list('test',
                                                                                                               flat=True).distinct()

        # Grant access to the course test if all module and lesson tests are passed
        all_tests_passed = all(test.id in passed_tests for test in all_tests)

        # Check if all homework has been submitted
        homeworks = Homework.objects.filter(lesson__module__course=course)
        submitted_homeworks = StudentHomework.objects.filter(student=user,
                                                             lesson__in=homeworks.values_list('lesson', flat=True))

        # Ensure the number of submitted homeworks matches the total number of homeworks for the course
        all_homeworks_submitted = submitted_homeworks.count() >= homeworks.count()

        # If any of the homework is missing or tests are not passed, block access to the final
        if all_tests_passed and all_homeworks_submitted:
            context['course_test_accessible'] = True
        else:
            context['course_test_accessible'] = False

        # Prepare accessible and blocked modules
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
        context['all_homeworks_submitted'] = all_homeworks_submitted

        # Course data for displaying
        modules = course.modules.all()  # Get all modules for the course
        lessons_count = 0
        for module in modules:
            lessons_count += module.lessons.count()  # Count lessons in each module

        course_data = {}
        course_data['modules_count'] = modules.count()  # Total number of modules
        course_data['lessons_count'] = lessons_count  # Total number of lessons
        course_data['course_hours'] = course.course_time

        context['course_data'] = course_data

        if not test:
            # No test for the lesson, call redirect to next step
            return self.redirect_to_next_step(module, course, lesson)

        return context

    def redirect_to_next_step(self, module, course, lesson):
        # 1. Check if literature exists for the lesson
        if lesson.literatures.exists():
            return redirect('courses:course_student_literature', course_id=course.id, module_id=module.id, lesson_id=lesson.id)

        # 2. If no literature, check if homework exists for the lesson
        homework = Homework.objects.filter(lesson=lesson).first()
        if homework:
            return redirect('courses:course_student_homework', course_id=course.id, module_id=module.id, lesson_id=lesson.id)

        # 3. If no literature or homework, redirect to the module test
        if module.tests.exists():
            return redirect('courses:course_student_test_module', course_id=course.id, module_id=module.id)

        # Fallback: If no test found, redirect back to the course overview or handle as needed
        return redirect('courses:course_overview', course_id=course.id)



class WelcomePageView(TemplateView):
    template_name = 'core/welcome.html'
