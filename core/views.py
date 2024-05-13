from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.views.generic import TemplateView, DetailView
from django.urls import reverse_lazy, reverse

from courses.models import Course, Module, Lesson


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
        modules = Module.objects.filter(course_id=self.object.id)
        context['modules_count'] = modules.count()
        lessons_count = 0
        for module in modules:
            lessons_count += Lesson.objects.filter(module_id=module.id).count()
        context["lessons_count"] = lessons_count
        context["courses"] = Course.objects.exclude(id=self.object.id)[:2]
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
        lesson = Lesson.objects.filter(lesson_name=self.kwargs['lesson_name'])
        module = Module.objects.filter(lessons__in=lesson).first()
        context['lesson'] = lesson.first()
        for i, item in enumerate(module.lessons.all()):
            print(item, type(item))
            if item == lesson.first():
                context['lesson_position'] = i+1
                break
        context['module_id'] = module.pk
        return context


class WelcomePageView(TemplateView):
    template_name = 'core/welcome.html'
