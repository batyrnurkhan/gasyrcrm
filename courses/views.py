import json
import traceback

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.contenttypes.models import ContentType
from django.db import IntegrityError, transaction
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse, HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, DetailView, View, TemplateView
from django.views.generic.edit import CreateView, FormView

from users.models import CustomUser
from .forms import CourseFormStep1, CourseFormStep2, LessonForm, TestForm, ModuleForm, AddStudentForm, CourseForm, \
    AnswerForm, QuestionForm, RatingForm
from .models import Course, Module, Lesson, Test, Question, Answer, TestSubmission, Rating


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

        if form.is_valid():
            course.course_name = form.cleaned_data["course_name"]
            course.mini_description = form.cleaned_data["mini_description"]
            course.big_description = form.cleaned_data["big_description"]
            course.course_time = form.cleaned_data["course_time"]
            course.course_difficulty = form.cleaned_data["course_difficulty"]
            course.full_description = form.cleaned_data["full_description"]

            if 'course_picture' in request.FILES:
                course.course_picture = form.cleaned_data["course_picture"]

            course.save()
            return redirect('courses:course_detail_edit', pk=course.id)

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
        content_type = ContentType.objects.get_for_model(parent_object)

        form = TestForm(request.POST, request.FILES)
        if form.is_valid():
            test = form.save(commit=False)
            test.content_object = parent_object
            test.save()

            questions_data = json.loads(request.POST.get('questions_data', '[]'))
            for question_data in questions_data:
                question_id = question_data.get('id')
                question_form = QuestionForm(question_data, request.FILES or None)
                if question_form.is_valid():
                    question = question_form.save(commit=False)
                    if question_id:
                        question.id = question_id
                    question.test = test
                    question.full_clean()  # This will trigger your custom validation in the model's clean method
                    question.save()

                    answers_data = question_data.get('answers', [])
                    for answer_data in answers_data:
                        answer_id = answer_data.get('id')
                        answer_form = AnswerForm(answer_data)
                        if answer_form.is_valid():
                            answer = answer_form.save(commit=False)
                            if answer_id:
                                answer.id = answer_id
                            answer.question = question
                            answer.save()
        if isinstance(parent_object, Course):
            redirect_url = reverse('courses:course_detail', kwargs={'pk': parent_object.pk})
        elif isinstance(parent_object, Module):
            redirect_url = reverse('courses:module_detail',
                                   kwargs={'pk': parent_object.pk})  # Assuming you have a view for module details
        elif hasattr(parent_object, 'module'):  # Likely a Lesson
            redirect_url = reverse('courses:module_detail', kwargs={'pk': parent_object.module.pk})

        return redirect(redirect_url)


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
    success_url = reverse_lazy('courses:add_students')

    def test_func(self):
        user = self.request.user
        return user.is_superuser or user.role == 'Teacher'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course_id = self.kwargs.get('pk')
        context['course'] = get_object_or_404(Course, pk=course_id)
        context['form'] = AddStudentForm(self.request.GET or None)

        # search_query = self.request.GET.get('search_query', '')
        # phone_number = self.request.GET.get('phone_number', '')
        login_code = self.request.GET.get('login_code', '')

        # if search_query:
        #     context['students'] = CustomUser.objects.filter(role='Student', full_name__icontains=search_query)
        # elif phone_number:
        #     context['students'] = CustomUser.objects.filter(role='Student', phone_number=phone_number)
        if login_code:
            context['students'] = CustomUser.objects.filter(role='Student', login_code=login_code)
        else:
            context['students'] = []

        return context

    def add_student_to_course(self, course_id, phone_number):
        course = get_object_or_404(Course, pk=course_id)
        student = get_object_or_404(CustomUser, phone_number=phone_number, role='Student')
        course.users.add(student)
        return HttpResponseRedirect(reverse_lazy('courses:course_detail', kwargs={'pk': course_id}))

    def form_valid(self, form):
        # Assuming the form is used to add students by name search
        search_query = form.cleaned_data.get('search_query')
        if search_query:
            students = CustomUser.objects.filter(full_name__icontains=search_query, role='Student')
            context = self.get_context_data(form=form, students=students)
            return self.render_to_response(context)
        return super().form_valid(form)

def add_student_to_course(request, course_id, student_id):
    if request.method == 'GET':
        course = get_object_or_404(Course, pk=course_id)
        student = get_object_or_404(CustomUser, pk=student_id)
        course.users.add(student)
        return JsonResponse({"message": "Student added successfully"}, status=200)
    else:
        return HttpResponseBadRequest("Invalid method")

def search_students(request):
    form = AddStudentForm(request.GET)
    if form.is_valid():
        students = CustomUser.objects.filter(login_code=form.cleaned_data['login_code'])
        html = render_to_string('courses/course/_student_list_partial.html', {'students': students}, request=request)
        return HttpResponse(html)
    else:
        return HttpResponseBadRequest('Invalid data', status=400)

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
        questions = test.questions.all()
        for question in questions:
            selected_answer_ids = list(map(int, request.POST.getlist(f'answer_{question.id}')))
            correct_answers = list(question.answers.filter(is_correct=True).values_list('id', flat=True))

            if not selected_answer_ids:
                continue

            # Handling Single and Multiple Choice
            if question.question_type in ['SC', 'MC']:
                selected_correct = set(selected_answer_ids).intersection(correct_answers)
                if len(selected_correct) == len(correct_answers) == len(selected_answer_ids):
                    score += 1

            elif question.question_type in ['IMG', 'AUD']:
                selected_correct = set(selected_answer_ids).intersection(correct_answers)
                if len(selected_correct) == len(correct_answers) == len(selected_answer_ids):
                    score += 1



        score_percentage = (score / total_questions) * 100 if total_questions else 0
        TestSubmission.objects.create(user=request.user, test=test, score=score_percentage)
        return redirect('courses:test_result', score=score_percentage)


def test_result_view(request, score):
    return render(request, 'courses/test_result.html', {'score': score})

@login_required
def list_students(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    if request.user.role != 'Teacher':
        return redirect('some_error_page')
    students = course.users.filter(role='Student')
    return render(request, 'courses/diary/list_students.html', {'students': students, 'course': course})

@login_required
def rate_student(request, course_id, student_id):
    course = get_object_or_404(Course, id=course_id)
    student = get_object_or_404(CustomUser, id=student_id)
    if request.user.role != 'Teacher' or not course.is_user_enrolled(student):
        return redirect('some_error_page')

    if request.method == 'POST':
        form = RatingForm(request.POST)
        if form.is_valid():
            rating, created = Rating.objects.update_or_create(
                course=course, student=student, teacher=request.user,
                defaults={'rating': form.cleaned_data['rating']}
            )
            return redirect('courses:list_students', course_id=course.id)
    else:
        form = RatingForm()

    return render(request, 'courses/diary/rate_student.html', {'form': form, 'course': course, 'student': student})