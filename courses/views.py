from django.http import HttpResponseBadRequest
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView

from .forms import CourseForm, ModuleForm, LessonForm, CourseFormStep2, CourseFormStep1, TestForm, QuestionForm, \
    AnswerForm
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView

from .models import Module, Lesson, Course, Test


def create_course_step1(request):
    if request.method == 'POST':
        form = CourseFormStep1(request.POST, request.FILES)
        if form.is_valid():
            # Save non-file fields in session
            course_step1_data = form.cleaned_data
            # Exclude the file field from what's stored in the session
            course_step1_data.pop('course_picture', None)
            request.session['course_step1_data'] = course_step1_data
            # Handle the file upload here or in the final step

            return redirect('courses:create_course_step2')
    else:
        form = CourseFormStep1()
    return render(request, 'courses/create_course_step1.html', {'form': form})

def create_course_step2(request):
    if request.method == 'POST':
        form = CourseFormStep2(request.POST)
        if form.is_valid():
            course_data = request.session.get('course_step1_data', {})
            course = Course(**course_data, **form.cleaned_data)
            course.created_by = request.user
            course.save()
            # Clear the session data
            del request.session['course_step1_data']
            return redirect('courses:course_detail', pk=course.pk)
    else:
        form = CourseFormStep2()
    return render(request, 'courses/create_course_step2.html', {'form': form})

class CourseListView(ListView):
    model = Course
    context_object_name = 'courses'
    template_name = 'courses/course_list.html'

class CourseDetailView(DetailView):
    model = Course
    context_object_name = 'course'
    template_name = 'courses/course_detail.html'

def create_course(request):
    if request.method == 'POST':
        form = CourseForm(request.POST, request.FILES)
        if form.is_valid():
            course = form.save(commit=False)
            course.created_by = request.user
            course.save()
            return redirect('courses:course_detail', pk=course.pk)
    else:
        form = CourseForm()
    return render(request, 'courses/create_course.html', {'form': form})


class ModuleDetailView(DetailView):
    model = Module
    context_object_name = 'module'
    template_name = 'courses/module_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Additional context data can be added here if needed
        return context

class ModuleCreateView(CreateView):
    model = Module
    form_class = ModuleForm
    template_name = 'courses/module_form.html'
    # Assuming you have a course_id URL keyword argument
    def form_valid(self, form):
        form.instance.course_id = self.kwargs['course_id']
        return super().form_valid(form)

    def get_success_url(self):
        # Redirect back to the course detail view
        return reverse_lazy('courses:course_detail', kwargs={'pk': self.kwargs['course_id']})

class LessonCreateView(CreateView):
    model = Lesson
    form_class = LessonForm
    template_name = 'courses/lesson_form.html'
    # Assuming you have a module_id URL keyword argument
    def form_valid(self, form):
        form.instance.module_id = self.kwargs['module_id']
        return super().form_valid(form)

    def get_success_url(self):
        # Redirect back to the module detail page
        return reverse_lazy('courses:module_detail', kwargs={'pk': self.kwargs['module_id']})

from django.contrib.contenttypes.models import ContentType

# def create_test(request, module_id=None, lesson_id=None):
#     if request.method == 'POST':
#         test_form = TestForm(request.POST)
#         question_form = QuestionForm(request.POST)
#         answer_form = AnswerForm(request.POST)
#         if test_form.is_valid() and question_form.is_valid() and answer_form.is_valid():
#             test = test_form.save(commit=False)
#             # Determine whether a Module or Lesson is the parent object
#             if module_id:
#                 parent_object = get_object_or_404(Module, pk=module_id)
#             elif lesson_id:
#                 parent_object = get_object_or_404(Lesson, pk=lesson_id)
#             else:
#                 return HttpResponseBadRequest("A module_id or lesson_id must be provided.")
#
#             # Set content_type and object_id for the Test instance
#             test.content_type = ContentType.objects.get_for_model(parent_object.__class__)
#             test.object_id = parent_object.pk
#             test.save()
#
#             # Now handle the creation of questions and answers here as needed
#
#             return redirect('courses:test_detail', pk=test.pk)
#     else:
#         test_form = TestForm()
#         question_form = QuestionForm()
#         answer_form = AnswerForm()
#
#     return render(request, 'courses/create_or_edit_test.html', {
#         'test_form': test_form,
#         'question_form': question_form,
#         'answer_form': answer_form,
#     })

class TestDetailView(DetailView):
    model = Test
    template_name = 'test_detail.html'
    context_object_name = 'test'

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        test_form = TestForm(request.POST, instance=self.object)
        if test_form.is_valid():
            test_form.save()
            return redirect(self.object.get_absolute_url())  # Implement get_absolute_url method in Test model
        # Handle question and answer forms similarly
        return self.render_to_response(self.get_context_data(form=test_form))

class LessonDetailView(DetailView):
    model = Lesson
    context_object_name = 'lesson'
    template_name = 'courses/lesson_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Additional context data can be added here if needed
        return context


# In your views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponse, HttpResponseBadRequest
from .models import Test, Question, Answer, Course, Module, Lesson
from django.views.decorators.csrf import csrf_exempt


def create_or_edit_test(request, parent_type, parent_id):
    parent_model = {'course': Course, 'module': Module, 'lesson': Lesson}.get(parent_type)
    if not parent_model:
        return HttpResponseBadRequest("Invalid parent type specified.")
    parent_object = get_object_or_404(parent_model, pk=parent_id)

    if request.method == 'POST':
        title = request.POST.get('title')
        # Retrieve or create the Test instance
        content_type = ContentType.objects.get_for_model(parent_object)
        test, created = Test.objects.get_or_create(
            content_type=content_type, object_id=parent_id,
            defaults={'title': title}
        )
        test.title = title  # Update the title if the test already exists
        test.save()

        # Iterate over questions
        for i in range(int(request.POST.get('question_count', 0))):
            question_text = request.POST.get(f'questions[{i}][text]', '')
            if question_text:
                question, _ = Question.objects.get_or_create(test=test, text=question_text)

                # Iterate over answers for each question
                for j in range(4):  # Assuming 4 answers per question
                    answer_text = request.POST.get(f'questions[{i}][answers][{j}][text]', '')
                    is_correct = request.POST.get(f'questions[{i}][answers][{j}][is_correct]', '') == 'on'
                    if answer_text:
                        Answer.objects.update_or_create(
                            question=question, text=answer_text,
                            defaults={'is_correct': is_correct}
                        )
        return redirect('courses:list')  # Adjust this to your actual success URL

    # Handling GET request
    else:
        return render(request, 'courses/create_or_edit_test.html', {
            'parent_type': parent_type,
            'parent_id': parent_id
        })
