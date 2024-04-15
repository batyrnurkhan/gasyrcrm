from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, View
from django.views.generic.edit import CreateView

from .forms import CourseFormStep1, CourseFormStep2, LessonForm, TestForm, ModuleForm
from .models import Course, Module, Lesson, Test, Question, Answer


class CreateCourseStep1View(View):
    def get(self, request, *args, **kwargs):
        form = CourseFormStep1()
        return render(request, 'courses/course/create_course_step1.html', {'form': form})

    def post(self, request, *args, **kwargs):
        form = CourseFormStep1(request.POST, request.FILES)
        if form.is_valid():
            course_step1_data = form.cleaned_data
            course_step1_data.pop('course_picture', None)
            request.session['course_step1_data'] = course_step1_data
            return redirect('courses:create_course_step2')
        return render(request, 'courses/course/create_course_step1.html', {'form': form})


class CreateCourseStep2View(View):
    def get(self, request, *args, **kwargs):
        form = CourseFormStep2()
        return render(request, 'courses/course/create_course_step2.html', {'form': form})

    def post(self, request, *args, **kwargs):
        form = CourseFormStep2(request.POST)
        if form.is_valid():
            course_data = request.session.get('course_step1_data', {})
            course = Course(**course_data, **form.cleaned_data)
            course.created_by = request.user
            course.save()
            del request.session['course_step1_data']
            return redirect('courses:course_detail', pk=course.pk)
        return render(request, 'courses/course/create_course_step2.html', {'form': form})


class CourseListView(ListView):
    model = Course
    context_object_name = 'courses'
    template_name = 'courses/course/course_list.html'


class CourseDetailView(DetailView):
    model = Course
    context_object_name = 'course'
    template_name = 'courses/course/course_detail.html'


class ModuleDetailView(DetailView):
    model = Module
    context_object_name = 'module'
    template_name = 'courses/module/module_detail.html'


class LessonCreateView(CreateView):
    model = Lesson
    form_class = LessonForm
    template_name = 'courses/lesson_form.html'

    def form_valid(self, form):
        form.instance.module_id = self.kwargs['module_id']
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('courses:module_detail', kwargs={'pk': self.kwargs['module_id']})


# class TestDetailView(DetailView):
#     model = Test
#     context_object_name = 'test'
#     template_name = 'test_detail.html'
#
#     def post(self, request, *args, **kwargs):
#         self.object = self.get_object()
#         test_form = TestForm(request.POST, instance=self.object)
#         if test_form.is_valid():
#             test_form.save()
#             return redirect(self.object.get_absolute_url())
#         return self.render_to_response(self.get_context_data(form=test_form))


class LessonDetailView(DetailView):
    model = Lesson
    context_object_name = 'lesson'
    template_name = 'courses/lesson_detail.html'


class CreateOrEditTestView(View):
    def get(self, request, parent_type, parent_id):
        parent_model = {'course': Course, 'module': Module, 'lesson': Lesson}.get(parent_type)
        if not parent_model:
            return HttpResponseBadRequest("Invalid parent type specified.")
        parent_object = get_object_or_404(parent_model, pk=parent_id)

        content_type = ContentType.objects.get_for_model(parent_object)
        test = Test.objects.filter(content_type=content_type, object_id=parent_id).first()

        return render(request, 'courses/create_or_edit_test.html', {
            'parent_type': parent_type,
            'parent_id': parent_id,
            'test': test,
            'test_exists': test is not None
        })

    def post(self, request, parent_type, parent_id):
        parent_model = {'course': Course, 'module': Module, 'lesson': Lesson}.get(parent_type)
        if not parent_model:
            return HttpResponseBadRequest("Invalid parent type specified.")
        parent_object = get_object_or_404(parent_model, pk=parent_id)

        title = request.POST.get('title')
        content_type = ContentType.objects.get_for_model(parent_object)
        test, created = Test.objects.get_or_create(
            content_type=content_type, object_id=parent_id,
            defaults={'title': title}
        )
        test.title = title
        test.save()

        for i in range(int(request.POST.get('question_count', 0))):
            question_text = request.POST.get(f'questions[{i}][text]', '')
            if question_text:
                question, _ = Question.objects.get_or_create(test=test, text=question_text)

                for j in range(4):
                    answer_text = request.POST.get(f'questions[{i}][answers][{j}][text]', '')
                    is_correct = request.POST.get(f'questions[{i}][answers][{j}][is_correct]', '') == 'on'
                    if answer_text:
                        Answer.objects.update_or_create(
                            question=question, text=answer_text,
                            defaults={'is_correct': is_correct}
                        )
        return redirect('courses:list')


class ModuleCreateView(CreateView):
    model = Module
    form_class = ModuleForm
    template_name = 'courses/module/module_form.html'

    def form_valid(self, form):
        form.instance.course_id = self.kwargs['course_id']
        return super().form_valid(form)

    def get_success_url(self):
        # Redirect back to the course detail view
        return reverse_lazy('courses:course_detail', kwargs={'pk': self.kwargs['course_id']})