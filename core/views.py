from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import redirect
from django.views.generic import TemplateView, DetailView
from django.urls import reverse_lazy, reverse
from django.db.models import Prefetch, Q

from courses.models import Course, Module, Lesson, TestSubmission, Test


class HomePageView(LoginRequiredMixin, TemplateView):

    def get_template_names(self):
        if self.request.user.role == "Teacher":
            return "core/teacher-home.html"
        else:
            return "core/student-home.html"

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        # Add in a QuerySet of all the books
        if self.request.user.role == "Teacher":
            context["courses"] = Course.objects.filter(created_by=self.request.user)
        else:
            context["courses"] = Course.objects.all()
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


class CoursePageView(LoginRequiredMixin, DetailView):
    model = Course
    template_name = 'core/course_detail.html'

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
        lesson = Lesson.objects.filter(module_id=module.pk).first()
    except:
        messages.error(request, "Course not found")
        return redirect(reverse("home"))
    return redirect(reverse("courses:course_start", kwargs={'pk': pk, 'lesson_name': lesson.lesson_name}))


class CourseStartPageView(LoginRequiredMixin, DetailView):
    model = Course
    template_name = 'core/student/course_start.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course = self.get_object()
        user = self.request.user

        modules = course.modules.prefetch_related(
            'tests',
            Prefetch('lessons', queryset=Lesson.objects.prefetch_related('tests'))
        )
        accessible_modules = []
        previous_module_passed = True  # First module is always accessible

        lesson_content_type = ContentType.objects.get_for_model(Lesson)

        for module in modules:
            module_tests = module.tests.all()
            lesson_tests = Test.objects.filter(
                content_type=lesson_content_type,
                object_id__in=module.lessons.values_list('id', flat=True)
            )

            all_tests = module_tests | lesson_tests

            if previous_module_passed:
                if all_tests.exists():
                    # Check if the user has passed all these tests
                    passed_tests = all_tests.filter(test_submissions__user=user,
                                                    test_submissions__score__gte=50).distinct()
                    user_passed_all_tests = passed_tests.count() == all_tests.count()

                    if user_passed_all_tests:
                        module.accessible = True
                    else:
                        module.accessible = False
                        previous_module_passed = False
                else:
                    module.accessible = True
            else:
                module.accessible = False

            accessible_modules.append(module)

        context['modules'] = accessible_modules
        return context

class WelcomePageView(TemplateView):
    template_name = 'core/welcome.html'
