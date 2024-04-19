import traceback

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.contenttypes.models import ContentType
from django.db import IntegrityError, transaction
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, DetailView, View, TemplateView
from django.views.generic.edit import CreateView, FormView

from users.models import CustomUser
from .forms import CourseFormStep1, CourseFormStep2, LessonForm, TestForm, ModuleForm, AddStudentForm, CourseForm
from .models import Course, Module, Lesson, Test, Question, Answer, TestSubmission


class CourseDelete(DetailView):
    model = Course

    def post(self, request, *args, **kwargs):
        pass


class EditCourseView(View):

    def get(self, request, *args, **kwargs):
        form = CourseForm()
        course = Course.objects.get(pk=self.kwargs["pk"])
        return render(request, 'courses/course/edit_course.html', {'form': form, 'course': course})

    def post(self, request, *args, **kwargs):
        form = CourseForm(request.POST, request.FILES)
        course = Course.objects.get(id=self.kwargs["pk"])
        print(form.data["course_name"])
        print(form.data["mini_description"])
        print(form.data["course_picture"])
        print(form.data["big_description"])
        print(form.data["course_time"])
        print(form.data["course_difficulty"])
        print(form.data["full_description"])
        print(form.is_valid())
        if form.is_valid():
            course.course_name = form.cleaned_data["course_name"]
            course.mini_description = form.cleaned_data["mini_description"]
            if form.cleaned_data["course_picture"]:
                course.course_picture = form.cleaned_data["course_picture"]
            course.big_description = form.cleaned_data["big_description"]
            course.course_time = form.cleaned_data["course_time"]
            course.course_difficulty = form.cleaned_data["course_difficulty"]
            course.full_description = form.cleaned_data["full_description"]
            return redirect('courses:course_detail_edit')
        return render(request, 'courses/course/edit_course.html', {'form': form, 'course': course})


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


from django.db.models import Prefetch


class CourseListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Course
    template_name = 'courses/course/course_list.html'
    context_object_name = 'courses'

    def test_func(self):
        return self.request.user.is_superuser or self.request.user.role in ['Student', 'Teacher']

    def get_queryset(self):
        user = self.request.user
        queryset = Course.objects.all()

        # Prefetch related modules and lessons to avoid N+1 queries
        queryset = queryset.prefetch_related(
            Prefetch('modules', queryset=Module.objects.prefetch_related('lessons'))
        )

        return queryset

    def post(self, request, *args, **kwargs):
        data_type = request.POST.get('data_type', 'all')
        user = self.request.user

        if data_type == 'mine':
            courses = user.courses.prefetch_related('modules__lessons')
        elif data_type == 'ended':
            courses = user.courses.prefetch_related('modules__lessons')
            courses = [course for course in courses if course.calculate_completion_percentage(user) >= 100]
        else:
            courses = self.get_queryset()

        for course in courses:
            course.completion_percentage = course.calculate_completion_percentage(user)

        context = {
            'course_data': [{'course': course, 'enrolled': True, 'completion': course.completion_percentage} for course
                            in courses]}
        html = render_to_string('courses/_course_list_partial.html', context, request=request)
        return JsonResponse({'html': html})


class CourseDetailView(LoginRequiredMixin, DetailView):
    model = Course
    template_name = 'courses/course/course_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course = self.get_object()
        user = self.request.user

        # Getting content type for Course
        course_type = ContentType.objects.get_for_model(course)
        test = Test.objects.filter(content_type=course_type, object_id=course.id).first()

        is_creator_or_superuser = user.is_superuser or course.created_by == user
        is_teacher = user.role == 'Teacher'
        is_enrolled = course.is_user_enrolled(user)

        context.update({
            'course': course,
            'test': test,
            'test_exists': test is not None,
            'creator_full_name': course.created_by.full_name,
            'creator_profile_picture': course.created_by.profile_picture.url if course.created_by.profile_picture else None,
            'can_modify_course': is_creator_or_superuser or is_teacher,
            'students': course.users.filter(role='Student').all() if is_creator_or_superuser or is_teacher else [],
            'is_enrolled': is_enrolled,
            'show_modules': is_enrolled or is_creator_or_superuser or is_teacher,
        })

        return context


class LessonCreateView(CreateView):
    model = Lesson
    form_class = LessonForm
    template_name = 'courses/lesson_form.html'

    def form_valid(self, form):
        form.instance.module_id = self.kwargs['module_id']
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('courses:module_detail', kwargs={'pk': self.kwargs['module_id']})


class ModuleDetailView(LoginRequiredMixin, DetailView):
    model = Module
    template_name = 'courses/module/module_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        module = self.get_object()
        test = module.tests.first()

        context['test'] = test
        context['test_exists'] = test is not None
        context['is_creator_or_superuser'] = user.is_superuser or user == module.course.created_by
        context['is_enrolled'] = module.course.users.filter(id=user.id).exists()

        return context


class LessonDetailView(DetailView):
    model = Lesson
    template_name = 'courses/lesson_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        lesson = self.get_object()
        user = self.request.user
        test = lesson.tests.first()

        context['test'] = test
        context['is_creator_or_superuser'] = user == lesson.module.course.created_by or user.is_superuser
        context['is_enrolled'] = lesson.module.course.users.filter(id=user.id).exists()

        return context


from django.contrib import messages
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
import logging

logger = logging.getLogger(__name__)


class CreateOrEditTestView(View):
    def get(self, request, parent_type, parent_id):
        parent_model = {'course': Course, 'module': Module, 'lesson': Lesson}.get(parent_type)
        parent_object = get_object_or_404(parent_model, pk=parent_id)
        content_type = ContentType.objects.get_for_model(parent_object)
        test = Test.objects.filter(content_type=content_type, object_id=parent_id).first()
        return render(request, 'courses/create_or_edit_test.html',
                      {'test': test, 'parent_object': parent_object, 'test_exists': test is not None})

    def post(self, request, parent_type, parent_id):
        parent_model = {'course': Course, 'module': Module, 'lesson': Lesson}.get(parent_type)
        parent_object = get_object_or_404(parent_model, pk=parent_id)
        title = request.POST.get('title')
        content_type = ContentType.objects.get_for_model(parent_object)

        test, created = Test.objects.get_or_create(
            content_type=content_type, object_id=parent_id,
            defaults={'title': title}
        )
        test.title = title
        test.save()

        question_count = int(request.POST.get('question_count', 0))
        for i in range(question_count):
            question_id = request.POST.get(f'questions[{i}][id]', None)
            question_text = request.POST.get(f'questions[{i}][text]', '')
            question_type = request.POST.get(f'questions[{i}][type]', 'SC')

            if question_text:
                question, _ = Question.objects.update_or_create(
                    id=question_id,
                    defaults={'test': test, 'text': question_text, 'question_type': question_type}
                )

                for j in range(4):
                    answer_id = request.POST.get(f'questions[{i}][answers][{j}][id]', None)
                    answer_text = request.POST.get(f'questions[{i}][answers][{j}][text]', '')
                    is_correct = f'questions[{i}][answers][{j}][is_correct]' in request.POST

                    if answer_text:
                        Answer.objects.update_or_create(
                            id=answer_id,
                            defaults={'question': question, 'text': answer_text, 'is_correct': is_correct}
                        )

        if isinstance(parent_object, Course):
            redirect_url = reverse('courses:course_detail', kwargs={'pk': parent_object.pk})
        elif isinstance(parent_object, Module):
            redirect_url = reverse('courses:module_detail',
                                   kwargs={'pk': parent_object.pk})  # Assuming you have a view for module details
        elif hasattr(parent_object, 'module'):  # Likely a Lesson
            redirect_url = reverse('courses:module_detail', kwargs={'pk': parent_object.module.pk})

        return redirect(redirect_url)  # Simplified redirection handling


class ModuleCreateView(CreateView):
    model = Module
    form_class = ModuleForm
    template_name = 'courses/module/module_form.html'

    def form_valid(self, form):
        form.instance.course_id = self.kwargs['course_id']
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('courses:course_detail_edit', kwargs={'pk': self.kwargs['course_id']})


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


from django.forms import modelformset_factory


class TakeTestView(LoginRequiredMixin, View):
    template_name = 'courses/take_test.html'

    def get(self, request, test_id):
        test = get_object_or_404(Test, pk=test_id)
        questions = test.questions.prefetch_related('answers').all()
        return render(request, self.template_name, {'test': test, 'questions': questions})

    def post(self, request, test_id):
        test = get_object_or_404(Test, pk=test_id)
        score = 0
        total_questions = test.questions.count()

        for question in test.questions.all():
            selected_answer_ids = request.POST.getlist(f'answer_{question.id}')
            correct_answers = question.answers.filter(is_correct=True).values_list('id', flat=True)

            if question.question_type == 'SC' and int(selected_answer_ids[0]) in correct_answers:
                score += 1
            elif question.question_type == 'MC' and all(
                    int(ans_id) in correct_answers for ans_id in selected_answer_ids) and len(
                selected_answer_ids) == len(correct_answers):
                score += 1

        score_percentage = (score / total_questions) * 100 if total_questions else 0
        TestSubmission.objects.create(user=request.user, test=test, score=score_percentage)
        return redirect('courses:test_result', score=score_percentage)


def test_result_view(request, score):
    return render(request, 'courses/test_result.html', {'score': score})
