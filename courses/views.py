from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, DetailView, View
from django.views.generic.edit import CreateView, FormView

from users.models import CustomUser
from .forms import CourseFormStep1, CourseFormStep2, LessonForm, TestForm, ModuleForm, AddStudentForm
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


class CourseListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Course
    template_name = 'courses/course/course_list.html'
    context_object_name = 'courses'

    def test_func(self):
        # Ensures that the user is a Student, Teacher, or Superuser
        return self.request.user.is_superuser or \
            self.request.user.role in ['Student', 'Teacher']

    def get_queryset(self):
        # Return all courses by default
        return Course.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Initially, display all courses
        context['my_courses'] = False
        return context

    def post(self, request, *args, **kwargs):
        # Check for an AJAX request
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            data_type = request.POST.get('data_type', 'all')
            if data_type == 'mine':
                courses = Course.objects.filter(users=request.user)
            else:
                courses = Course.objects.all()
            context = {'courses': courses, 'my_courses': data_type == 'mine'}

            # Render your course list part of the template with updated context
            courses_html = render_to_string('courses/_course_list_partial.html', context, request)
            return JsonResponse({'courses_html': courses_html})
        else:
            return HttpResponseBadRequest("This endpoint only supports AJAX requests.")



class CourseDetailView(DetailView):
    model = Course
    template_name = 'courses/course/course_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        if hasattr(self.object, 'is_user_enrolled'):
            context['is_user_enrolled'] = self.object.is_user_enrolled(user)
        else:
            context['is_user_enrolled'] = False
        context['can_add_students'] = user.is_superuser or user.role == 'Teacher'
        context['students'] = self.object.users.filter(role='Student')
        return context


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

        # Handling existing questions
        existing_question_ids = [int(q_id) for q_id in request.POST.getlist('question_ids', [])]
        if not created:
            # Delete any questions not included in the current submission
            test.questions.exclude(id__in=existing_question_ids).delete()

        for i in range(int(request.POST.get('question_count', 0))):
            question_id = request.POST.get(f'questions[{i}][id]', None)
            question_text = request.POST.get(f'questions[{i}][text]', '')
            question_type = request.POST.get(f'questions[{i}][type]', 'SC')

            if question_text:
                if question_id:
                    question = Question.objects.get(id=int(question_id))
                    question.text = question_text
                    question.question_type = question_type
                    question.save()
                else:
                    question = Question.objects.create(test=test, text=question_text, question_type=question_type)

                # Update answers
                for j in range(4):  # assuming there are always four answers
                    answer_id = request.POST.get(f'questions[{i}][answers][{j}][id]', None)
                    answer_text = request.POST.get(f'questions[{i}][answers][{j}][text]', '')
                    is_correct = request.POST.get(f'questions[{i}][answers][{j}][is_correct]', '') == 'on'

                    if answer_text:
                        if answer_id:
                            answer = Answer.objects.get(id=int(answer_id))
                            answer.text = answer_text
                            answer.is_correct = is_correct
                            answer.save()
                        else:
                            Answer.objects.create(question=question, text=answer_text, is_correct=is_correct)

        return redirect('courses:list')


class ModuleCreateView(CreateView):
    model = Module
    form_class = ModuleForm
    template_name = 'courses/module/module_form.html'

    def form_valid(self, form):
        form.instance.course_id = self.kwargs['course_id']
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('courses:course_detail', kwargs={'pk': self.kwargs['course_id']})

class AddStudentsView(LoginRequiredMixin, UserPassesTestMixin, FormView):
    template_name = 'courses/course/add_students.html'
    form_class = AddStudentForm
    success_url = reverse_lazy('courses:add_students')  # Make sure this URL is correctly configured

    def test_func(self):
        user = self.request.user
        return user.is_superuser or user.role == 'Teacher'

    def get(self, request, *args, **kwargs):
        # This ensures that the GET method can also handle adding a student if 'add_student_phone' is in the query.
        if 'add_student_phone' in request.GET:
            phone_number = request.GET.get('add_student_phone')
            return self.add_student_to_course(self.kwargs['pk'], phone_number)
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def add_student_to_course(request, course_id, student_id):
        course = get_object_or_404(Course, pk=course_id)
        student = get_object_or_404(CustomUser, pk=student_id, role='Student')
        course.users.add(student)
        return redirect('courses:course_detail', pk=course_id)

    def form_valid(self, form):
        # When the form is valid, process the search and update the context with the results
        search_query = form.cleaned_data['search_query']
        students = CustomUser.objects.filter(full_name__icontains=search_query, role='Student')
        context = self.get_context_data(form=form, students=students)
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course_id = self.kwargs.get('pk')
        course = get_object_or_404(Course, pk=course_id)
        context['course'] = course

        # Initialize the form in context data for re-rendering the page on GET requests.
        context['form'] = AddStudentForm(self.request.GET or None)

        if 'search_query' in self.request.GET:
            search_query = self.request.GET['search_query']
            context['students'] = CustomUser.objects.filter(role='Student', full_name__icontains=search_query)
        else:
            context['students'] = []

        return context

def add_student_to_course(request, course_id, student_id):
    course = get_object_or_404(Course, pk=course_id)
    student = get_object_or_404(CustomUser, pk=student_id)
    course.users.add(student)  # Assuming 'users' is the ManyToMany field relating courses to students
    return redirect('courses:course_detail', pk=course_id)