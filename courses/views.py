import json
import traceback

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.contenttypes.models import ContentType
from django.db import IntegrityError, transaction
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse, HttpResponseRedirect, \
    HttpResponseNotAllowed, Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse_lazy, reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.views.generic import ListView, DetailView, View, TemplateView
from django.views.generic.edit import CreateView, FormView, UpdateView
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from users.models import CustomUser
from .forms import CourseFormStep1, CourseFormStep2, LessonForm, TestForm, ModuleForm, AddStudentForm, CourseForm, \
    AnswerForm, QuestionForm
from .models import Course, Module, Lesson, Test, Question, Answer, TestSubmission, LessonLiterature
from .serializers import CourseSerializer, ModuleSerializer, LessonSerializer, LiteratureSerializer


class CourseDelete(DetailView):
    model = Course

    def post(self, request, *args, **kwargs):
        pass


class EditCourseView(View):

    def get(self, request, *args, **kwargs):
        course = Course.objects.get(pk=self.kwargs["pk"])
        form = CourseForm(instance=course)
        return render(request, 'courses/course/edit_course.html', {'form': form, 'course': course})

    def post(self, request, *args, **kwargs):
        form = CourseForm(request.POST, request.FILES)
        course = Course.objects.get(id=self.kwargs["pk"])
        print(form.is_valid())
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

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            module_form = ModuleForm(request.POST, request.FILES)
            if module_form.is_valid():
                new_module = module_form.save(commit=False)
                new_module.course_id = self.kwargs["pk"]
                new_module.save()
                return JsonResponse({'module_id': new_module.id, 'module_name': new_module.name}, status=200)
            else:
                return JsonResponse({'error': module_form.errors}, status=400)

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
            return redirect('courses:create_course_step3', course_id=course.id)
        return render(request, 'courses/course/create_course_step2.html', {'form': form})


class CreateCourseStep3View(View):
    def get(self, request, *args, **kwargs):
        course = Course.objects.get(id=self.kwargs["course_id"])
        return render(request, 'courses/course/create_course_step3.html', {'course': course})


class CreateCourseStep4View(View):
    def get(self, request, *args, **kwargs):
        course = Course.objects.get(id=self.kwargs["course_id"])
        return render(request, 'courses/course/create_course_step4.html', {'course': course})


class CreateCourseStep5View(View):
    def get(self, request, *args, **kwargs):
        course = Course.objects.get(id=self.kwargs["course_id"])
        return render(request, 'courses/course/create_course_step5.html', {'course': course})


class CreateCourseEndingView(View):
    def get(self, request, *args, **kwargs):
        course = Course.objects.get(id=self.kwargs["course_id"])
        return render(request, 'courses/course/create_course_ending.html', {'course': course})


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
        module = self.get_object()
        if module is None:
            raise Http404("Module not found")
        user = self.request.user
        test = module.tests.first()
        course = module.course
        module_index_gen = (i for i, v in enumerate(course.modules.all()) if v.id == module.id)
        module_index = next(module_index_gen, 0) + 1  # default to 0 if not found
        context.update({
            'test': test,
            'module_index': module_index,
            'course': course,
            'test_exists': test is not None,
            'is_creator_or_superuser': user.is_superuser or user == module.course.created_by,
            'is_enrolled': module.course.users.filter(id=user.id).exists(),
        })
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


class CreateOrEditTestView(View, LoginRequiredMixin):
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

        existing_test = Test.objects.filter(content_type=content_type, object_id=parent_id).first()
        form = TestForm(request.POST, request.FILES, instance=existing_test)

        if form.is_valid():
            test = form.save(commit=False)
            test.content_object = parent_object
            test.save()

            # Collect existing question IDs for deletion check
            existing_question_ids = {question.id for question in test.questions.all()}
            question_count = int(request.POST.get('question_count', 0))

            for i in range(question_count):
                question_id = request.POST.get(f'questions[{i}][id]', None)
                question_data = {
                    'text': request.POST.get(f'questions[{i}][text]'),
                    'question_type': request.POST.get(f'questions[{i}][type]'),
                    'image': request.FILES.get(f'questions[{i}][image]') if 'IMG' in request.POST.get(
                        f'questions[{i}][type]', '') else None,
                    'audio': request.FILES.get(f'questions[{i}][audio]') if 'AUD' in request.POST.get(
                        f'questions[{i}][type]', '') else None
                }
                print(question_data)
                if question_id:
                    question = Question.objects.get(id=question_id)
                #     question_form = QuestionForm(question_data, request.FILES, instance=question)
                # else:
                #     question_form = QuestionForm(question_data, request.FILES)
                # print(question_form.is_valid())
                # print(question_form.errors)
                # if question_form.is_valid():
                #     question = question_form.save(commit=False)
                else:
                    question = Question()
                question.text = question_data["text"]
                question.question_type = question_data["question_type"]
                if question_data["question_type"] == "IMG" and question_data["image"]:
                    question.image = question_data["image"]
                    question.audio = None
                if question_data["question_type"] == "AUD" and question_data["audio"]:
                    question.image = None
                    question.audio = question_data["audio"]
                if question_data["question_type"] == "MC" or question_data["question_type"] == "SC":
                    question.image = None
                    question.audio = None

                question.test = test
                question.save()
                existing_question_ids.discard(question.id)

                existing_answer_ids = {answer.id for answer in question.answers.all()}
                answer_index = 0
                while True:
                    answer_text = request.POST.get(f'questions[{i}][answers][{answer_index}][text]', None)
                    if answer_text is None:
                        break
                    answer_id = request.POST.get(f'questions[{i}][answers][{answer_index}][id]', None)
                    answer_data = {
                        'text': answer_text,
                        'is_correct': 'on' in request.POST.get(
                            f'questions[{i}][answers][{answer_index}][is_correct]', '')
                    }
                    if answer_id:
                        answer = Answer.objects.get(id=answer_id)
                        answer_form = AnswerForm(answer_data, instance=answer)
                    else:
                        answer_form = AnswerForm(answer_data)

                    if answer_form.is_valid():
                        answer = answer_form.save(commit=False)
                        answer.question = question
                        answer.save()
                        existing_answer_ids.discard(answer.id)  # Remove from set for deletion check
                    answer_index += 1

                Answer.objects.filter(id__in=existing_answer_ids).delete()

            Question.objects.filter(id__in=existing_question_ids).delete()

        else:
            print(form.errors)

        if isinstance(parent_object, Course):
            redirect_url = reverse('courses:course_detail_edit', kwargs={'pk': parent_object.pk})
        elif isinstance(parent_object, Module):
            redirect_url = reverse('home')  # Ensure no kwargs are passed here
        elif hasattr(parent_object, 'module'):
            redirect_url = reverse('home')

        return redirect(redirect_url)


class CourseModulesView(APIView):
    def get(self, request, course_id):
        course = Course.objects.filter(id=course_id).first()
        if course:
            serializer = CourseSerializer(course)
            return Response(serializer.data)
        return Response({'error': 'Course not found'}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, course_id):
        course = Course.objects.get(pk=course_id)
        serializer = CourseSerializer(course, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ModuleCreateViewAPI(APIView):
    def post(self, request, course_id):
        # Fetch the course based on the provided course_id
        course = Course.objects.filter(id=course_id).first()
        if not course:
            return Response({'error': 'Course not found'}, status=status.HTTP_404_NOT_FOUND)

        # Include course data in request data
        request.data['course'] = course_id

        # Serialize data
        serializer = ModuleSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LessonCreateViewAPI(APIView):
    def post(self, request, module_id):
        # Fetch the course based on the provided course_id
        course = Module.objects.filter(id=module_id).first()
        if not course:
            return Response({'error': 'Module not found'}, status=status.HTTP_404_NOT_FOUND)

        # Include course data in request data
        request.data['module'] = module_id

        # Serialize data
        serializer = LessonSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LiteratureCreateViewAPI(APIView):
    def post(self, request, lesson_id):
        # Check if the lesson exists
        if not Lesson.objects.filter(id=lesson_id).exists():
            return Response({'error': 'Lesson not found'}, status=status.HTTP_404_NOT_FOUND)

        # Add lesson to the request data
        request.data["lesson"] = lesson_id
        serializer = LiteratureSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LiteratureDeleteViewAPI(APIView):
    def delete(self, request, literature_id):
        # Add lesson to the request data
        LessonLiterature.objects.get(id=literature_id).delete()
        return Response({"message": "Delete complete"}, status=status.HTTP_200_OK)


class ModuleDeleteViewAPI(APIView):
    def delete(self, request, module_id):
        # Add lesson to the request data
        Module.objects.get(id=module_id).delete()
        return Response({"message": "Delete complete"}, status=status.HTTP_200_OK)


class LessonDeleteViewAPI(APIView):
    def delete(self, request, lesson_id):
        # Add lesson to the request data
        Lesson.objects.get(id=lesson_id).delete()
        return Response({"message": "Delete complete"}, status=status.HTTP_200_OK)


class ModuleCreateView(CreateView):
    model = Module
    form_class = ModuleForm
    template_name = 'courses/module/module_form.html'

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.course_id = self.kwargs['course_id']
        self.object.save()
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # Return JSON response if this is an AJAX request
            return JsonResponse({
                'module_id': self.object.id,
                'module_name': self.object.module_name  # Corrected field name here
            }, status=200)
        else:
            # Perform a redirect on successful save
            return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        # Redirect to the detail view of the newly created module
        return reverse_lazy('courses:module_detail', kwargs={'pk': self.object.id})


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
        all_selected_answer_ids = []
        for question in questions:
            selected_answer_ids = list(map(int, request.POST.getlist(f'answer_{question.id}')))
            all_selected_answer_ids.extend(selected_answer_ids)  # Extending instead of appending to flatten the list
            correct_answers = list(question.answers.filter(is_correct=True).values_list('id', flat=True))

            # Adjusted logic to handle multiple correct answers
            if question.question_type in ['SC', 'MC']:
                if set(selected_answer_ids) == set(correct_answers):
                    score += 1

            elif question.question_type in ['IMG', 'AUD']:
                selected_correct = set(selected_answer_ids).intersection(correct_answers)
                if len(selected_correct) == len(correct_answers) == len(selected_answer_ids):
                    score += 1

        selected_answers = Answer.objects.filter(id__in=all_selected_answer_ids)
        score_percentage = (score / total_questions) * 100 if total_questions else 0
        test_submission = TestSubmission.objects.create(user=request.user, test=test, score=score_percentage)
        test_submission.selected_answers.add(*selected_answers)
        return redirect('courses:test_result', score=score_percentage)


def student_results_view(request, course_id, student_login_code):
    student = CustomUser.objects.get(login_code=student_login_code)
    course = Course.objects.get(id=course_id)
    context = {'student': student, 'course': course}
    course_tests = Test.objects.filter(object_id=course_id)
    modules = Module.objects.filter(course_id=course_id)
    module_tests = Test.objects.filter(object_id__in=modules.values_list('id', flat=True))
    lessons = Lesson.objects.filter(module__course_id=course_id)
    lesson_tests = Test.objects.filter(object_id__in=lessons.values_list('id', flat=True))
    context['sub_test_lesson'] = TestSubmission.objects.filter(user=student, test__in=lesson_tests)
    context['sub_test_module'] = TestSubmission.objects.filter(user=student, test__in=module_tests)
    context['sub_test_course'] = TestSubmission.objects.filter(user=student, test__in=course_tests)
    return render(request, 'courses/student_results.html', context)


def test_result_view(request, score):
    return render(request, 'courses/test_result.html', {'score': score})


class CourseFinalTestView(DetailView):
    model = Course
    template_name = 'courses/course/final-test-edit.html'


class SuccessVideoLinkEditView(DetailView):
    model = Course
    template_name = 'courses/course/success-video-link-edit.html'


@csrf_exempt
@require_http_methods(["DELETE"])
def delete_literature(request):
    try:
        # Convert body data from bytes to a string, then to a dictionary
        print(request.body.decode('utf-8'))
        data = json.loads(request.body.decode('utf-8'))
        literature_id = data.get('id')

        # Fetch the literature instance
        literature = LessonLiterature.objects.get(id=literature_id)

        # Delete the instance
        literature.delete()

        # Return a success response
        return JsonResponse({'message': 'Literature deleted successfully'}, status=200)
    except LessonLiterature.DoesNotExist:
        # Return an error response if the literature does not exist
        return JsonResponse({'error': 'Literature not found'}, status=404)
    except Exception as e:
        # Return an error response for any other exceptions
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["POST"])
def bulk_create_lessons(request, module_id):
    module = get_object_or_404(Module, pk=module_id)
    lessons_data = list(zip(request.POST.getlist('lesson_names[]'), request.POST.getlist('video_links[]')))
    lessons_data = [data for data in lessons_data if all(data)]  # Filter out empty pairs

    if not lessons_data:
        return JsonResponse({'status': 'error', 'errors': 'No data provided.'}, status=400)

    created_lessons = []
    errors = []

    for lesson_name, video_link in lessons_data:
        form = LessonForm(data={'lesson_name': lesson_name, 'video_link': video_link})
        if form.is_valid():
            lesson = form.save(commit=False)
            lesson.module = module
            lesson.save()
            created_lessons.append(lesson)
        else:
            errors.append(form.errors)

    if errors:
        return JsonResponse({'status': 'error', 'errors': errors}, status=400)

    return JsonResponse({'status': 'success', 'message': f'{len(created_lessons)} lessons created successfully'})


@require_http_methods(["POST"])
def update_module_and_lessons(request, module_id):
    module = get_object_or_404(Module, pk=module_id)
    module_form = ModuleForm(request.POST, instance=module)
    if module_form.is_valid():
        module_form.save()
    else:
        return JsonResponse({'status': 'error', 'errors': module_form.errors}, status=400)

    lessons_data = list(zip(request.POST.getlist('lesson_names[]'), request.POST.getlist('video_links[]')))
    updated_lessons = []
    errors = []

    for lesson_name, video_link in lessons_data:
        # Optionally include lesson IDs if updating existing lessons
        lesson_id = request.POST.get('lesson_id[]')  # Update accordingly if you have lesson IDs passed
        lesson = Lesson.objects.get(id=lesson_id) if lesson_id else Lesson(module=module)
        form = LessonForm(data={'lesson_name': lesson_name, 'video_link': video_link}, instance=lesson)

        if form.is_valid():
            form.save()
            updated_lessons.append(lesson)
        else:
            errors.extend(form.errors)

    if errors:
        return JsonResponse({'status': 'error', 'errors': errors}, status=400)

    return JsonResponse({'status': 'success',
                         'message': f'{len(updated_lessons)} lessons updated/created successfully, module updated'})


def publishCourse(request, pk):
    course = Course.objects.get(pk=pk)
    course.published = not course.published
    course.save()
    return redirect('courses:course_detail_edit', pk=pk)
