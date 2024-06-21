import datetime
import logging
from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Prefetch, Q
from django.http import JsonResponse, HttpResponseForbidden, Http404, FileResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.utils import json

from appointments.forms import AppointmentForm
from appointments.models import Appointment
from chats.models import ChatRoom, Message
from schedule.models import ShiftTime, Shift
from users.models import CustomUser
from .forms import TaskForm, LessonForm, GroupTemplateForm, UserSearchForm, VolunteerChannelForm, GradeForm, \
    FileUploadForm, AchievementForm, StudentAchievementForm
from .models import Subject, GroupTemplate, Lesson_crm2, Task, VolunteerChannel, Grade, TaskSubmission, \
    StudentAchievement, Achievement
from .serializers import FileUploadSerializer, TaskSubmissionSerializer


@login_required
def home_view(request):
    user = request.user
    context = {}

    if user.role == 'Mentor':
        template_name = 'subjects/mentor-home.html'
    elif user.role == 'Teacher':
        template_name = 'subjects/teacher-home.html'
    elif user.role == 'Psychologist':
        today = datetime.now().date()
        start_of_week = today - timedelta(days=today.weekday())  # Ensure Monday is day 0
        dates_of_week = [start_of_week + timedelta(days=i) for i in range(6)]  # Get Monday to Saturday

        context = {
            'dates_of_week': dates_of_week,
        }
        template_name = 'appointments/week_view.html'
    else:
        user_lessons = Lesson_crm2.objects.filter(
            group_template__students=user
        ).select_related('teacher', 'subject', 'chat_room')
        print("Debug - User Lessons with Chat Rooms:",
              [(lesson.group_name, lesson.chat_room) for lesson in user_lessons])

        last_task = Task.objects.filter(
            chat_room__in=[lesson.chat_room for lesson in user_lessons]
        ).select_related('created_by').order_by('-deadline').first()

        print("Debug - Last Task Details:", last_task)

        if last_task:
            task_teacher = last_task.created_by
            creator_profile_pic_url = task_teacher.profile_picture.url if task_teacher.profile_picture else None
            subject_name = last_task.chat_room.lessons.first().subject.name if last_task.chat_room.lessons.exists() else "No Subject"
        else:
            task_teacher = None
            creator_profile_pic_url = None
            subject_name = "No Subject"
        template_name = 'subjects/home.html'
        context = {
            'task_teacher': task_teacher,
            'creator_profile_pic_url': creator_profile_pic_url,
            'subject_name': subject_name,
            'last_task': last_task
        }

    return render(request, template_name, context)


@login_required
def tasks_view(request):
    user = request.user
    # Get all tasks related to the lessons where the user is a student
    tasks = Task.objects.filter(chat_room__lessons__group_template__students=user).order_by('-deadline')

    return render(request, 'subjects/tasks.html', {
        'tasks': tasks
    })


@login_required
def mini_schedule_view(request):
    user = request.user
    if user.role == 'Mentor':
        shifts = Shift.objects.prefetch_related(
            'times__lessons',
            'times__lessons__teacher'
        ).all()

        if not shifts:
            print("No shifts found.")
        else:
            print(f"Found {len(shifts)} shifts.")

        return render(request, 'schedule/shifts.html', {'shifts': shifts})

    today = timezone.now().date()
    current_weekday = today.weekday()
    weeknames = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

    next_three_days = weeknames[current_weekday:current_weekday + 3] if current_weekday <= 4 else weeknames[
                                                                                                  current_weekday:] + weeknames[
                                                                                                                      :current_weekday + 3 - 7]
    weekly_lessons = {day: [] for day in next_three_days}

    student_groups = GroupTemplate.objects.filter(students=user)
    lessons = Lesson_crm2.objects.filter(group_template__in=student_groups)

    for lesson in lessons:
        lesson_weekday = lesson.time_slot.date.weekday()
        lesson_day_name = weeknames[lesson_weekday]
        if lesson_day_name in weekly_lessons:
            weekly_lessons[lesson_day_name].append(lesson)

    week_dates = {weeknames[i]: today + timedelta(days=i - current_weekday) for i in range(current_weekday, current_weekday + 3) if i < 7}

    print(week_dates)
    print(weekly_lessons)
    return render(request, 'subjects/mini_schedule.html', {
        'weekly_lessons': weekly_lessons,
        'week_dates': week_dates
    })

@login_required
def weekly_schedule_view(request):
    user = request.user
    # еСЛИ ЮЗЕР СУПЕРАДМИН ИЛИ МЕНТОР ЕГО ПЕРЕНАПРАВЛЯЮТ В SUBJECS/VIEWS.PY
    if user.role == 'Mentor':
        shifts = Shift.objects.prefetch_related(
            'times__lessons',
            'times__lessons__teacher'
        ).all()

        if not shifts:
            print("No shifts found.")
        else:
            print(f"Found {len(shifts)} shifts.")

        return render(request, 'schedule/shifts.html', {'shifts': shifts, 'page': "schedule"})

    today = timezone.now().date()
    start_of_week = today - timedelta(days=today.weekday())
    weeknames = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресение']

    weekly_lessons = {day: [] for day in weeknames}

    student_groups = GroupTemplate.objects.filter(students=user)
    lessons = Lesson_crm2.objects.filter(group_template__in=student_groups)

    for lesson in lessons:
        lesson_weekday = lesson.time_slot.date.weekday()
        lesson_day_name = weeknames[lesson_weekday]
        weekly_lessons[lesson_day_name].append(lesson)

    week_dates = {weeknames[i]: start_of_week + timedelta(days=i) for i in range(7)}

    return render(request, 'subjects/weekly_schedule.html', {
        'weekly_lessons': weekly_lessons,
        'week_dates': week_dates,
        'page': "schedule"
    })

@login_required
def group_templates_view(request):
    group_templates = GroupTemplate.objects.prefetch_related('students').all()
    student_count = CustomUser.objects.filter(role='Student').count()
    students = CustomUser.objects.filter(role='Student').order_by('full_name')[:8]

    search_query = request.GET.get('search', '')
    if search_query:
        students = CustomUser.objects.filter(
            Q(full_name__icontains=search_query) | Q(phone_number__icontains=search_query),
            role='Student'
        ).order_by('full_name')[:8]

    context = {
        'page': 'students',
        'group_templates': group_templates,
        'student_count': student_count,
        'students': students,
        'search_query': search_query
    }
    return render(request, 'subjects/group-templates.html', context)

class EditGroupTemplateView(UpdateView):
    model = GroupTemplate
    form_class = GroupTemplateForm
    template_name = 'subjects/edit_group_template.html'
    context_object_name = 'template'

    def get_success_url(self):
        return reverse('group_templates_view')

class SubjectListView(ListView):
    model = Lesson_crm2
    template_name = 'subjects/subject_list.html'
    context_object_name = 'lessons'

    def get_queryset(self):
        # Ensuring only lessons where the user is part of the group template are shown
        return Lesson_crm2.objects.filter(
            group_template__students=self.request.user
        ).select_related('mentor', 'teacher', 'subject')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page'] = "online-classes"
        return context


@login_required
def group_template_list(request):
    form = GroupTemplateForm(request.POST or None)
    search_form = UserSearchForm(request.GET or None)

    # Fetch all group templates
    group_templates = GroupTemplate.objects.all()

    # Default fetch top 8 students alphabetically
    students = CustomUser.objects.filter(role='Student').order_by('full_name')[:8]

    # If there is a valid search query, filter by both full name and phone number
    if 'search' in request.GET and search_form.is_valid():
        search_query = request.GET.get('search', '')
        students = CustomUser.objects.filter(
            Q(full_name__icontains=search_query) | Q(phone_number__icontains=search_query),
            role='Student'
        ).order_by('full_name')[:8]

    # If the form is submitted to create a new group template
    if request.method == 'POST' and 'create_template' in request.POST:
        print("Here")
        if form.is_valid():
            print("Here")
            group_template = form.save(commit=False)
            selected_students = request.POST.getlist('selected_students')
            group_template.save()
            group_template.students.set(selected_students)
            return redirect('subjects:group_templates_view')  # Redirect to avoid double POST on refresh

    return render(request, 'subjects/group_template_list.html', {
        'form': form,
        'search_form': search_form,
        'students': students,
        'group_templates': group_templates
    })

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView
from .models import Lesson_crm2
from django.utils import timezone

class LessonListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Lesson_crm2
    template_name = 'subjects/lesson_list.html'
    context_object_name = 'lessons'

    def test_func(self):
        # Check if user is a student or a superuser
        return self.request.user.is_superuser or self.request.user.role == 'Student'

    def get_queryset(self):
        # Superusers see all lessons, students see only their lessons
        if self.request.user.is_superuser:
            return Lesson_crm2.objects.all().select_related('teacher', 'time_slot')
        return Lesson_crm2.objects.filter(group_template__students=self.request.user).select_related('teacher',
                                                                                                     'time_slot')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['now'] = timezone.now()  # if you need the current time
        return context

class LessonCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Lesson_crm2
    form_class = LessonForm
    template_name = 'subjects/lesson_create.html'

    def test_func(self):
        # Check if the user is authenticated and is a mentor
        return self.request.user.is_authenticated and self.request.user.role == 'Mentor'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['time_id'] = self.kwargs['time_id']
        return context

    def form_valid(self, form):
        try:
            time_slot = ShiftTime.objects.get(pk=self.kwargs['time_id'])
        except ShiftTime.DoesNotExist:
            raise Http404("Time slot does not exist")
        form.instance.time_slot = time_slot

        form.instance.mentor = self.request.user  # Set the mentor as the current user
        form.instance.time_slot_id = self.kwargs['time_id']  # Set the time_slot from the URL parameter

        # Create a chat room for the lesson
        chat_room = ChatRoom.objects.create(title="Temporary Title")
        form.instance.chat_room = chat_room  # Associate the chat room with the lesson

        response = super().form_valid(form)  # Save the lesson and form data

        # Update the chat room title and save it
        chat_room.title = f"Lesson {self.object.id} Chat"
        chat_room.save()

        # Add users to chat room
        for student in self.object.group_template.students.all():
            chat_room.participants.add(student)
        if self.object.teacher:
            chat_room.participants.add(self.object.teacher)

        return response

    def get_success_url(self):
        # Redirects back to the shifts page after successful creation
        return reverse('schedule:shifts')

class LessonDetailView(DetailView):
    model = Lesson_crm2
    template_name = 'subjects/lesson_detail.html'

    def get_object(self):
        lesson = super().get_object()
        # Optionally, check permissions here
        return lesson

from django.utils.timezone import make_aware
from datetime import datetime


@login_required
def create_task(request, room_id):
    room = get_object_or_404(ChatRoom, id=room_id)
    if request.method == 'POST':
        name = request.POST.get('name')
        deadline_date = request.POST.get('deadline_date')
        deadline_time = request.POST.get('deadline_time')
        file = request.FILES.get('file')

        deadline_str = f"{deadline_date} {deadline_time}"
        deadline = make_aware(datetime.strptime(deadline_str, '%Y-%m-%d %H:%M'))

        task = Task.objects.create(
            name=name,
            deadline=deadline,
            file=file,
            chat_room=room,
            created_by=request.user
        )

        # Create a message in the chat
        message_content = f"Задание от учителя: {task.name} - {task.deadline.strftime('%Y-%m-%d %H:%M')}"
        if task.file:
            message_content += f" <a href='{task.file.url}'>Download</a>"

        Message.objects.create(
            chat_room=room,
            user=request.user,
            message=message_content,
            message_type='task',
            file=task.file if task.file else None,
            task=task
        )

        return redirect('chats:chat_room_detail', room_id=room_id)
    else:
        form = TaskForm()

    tasks = Task.objects.filter(chat_room=room).order_by('-deadline')
    return render(request, 'subjects/create_task.html', {
        'form': form,
        'room': room,
        'tasks': tasks
    })


def search_students(request):
    search_term = request.GET.get('search', '')
    students = CustomUser.objects.filter(
        role='Student',
        full_name__icontains=search_term
    ).order_by('full_name')[:10]

    student_list = list(students.values('id', 'full_name'))
    return JsonResponse(student_list, safe=False)


@login_required
def set_grade(request, lesson_id):
    lesson = get_object_or_404(Lesson_crm2, id=lesson_id)
    students = lesson.group_template.students.all()

    # Get the date from the query parameter, default to today if not provided
    date_str = request.GET.get('day')
    if date_str:
        day = timezone.datetime.strptime(date_str, '%m.%d.%Y').date()
    else:
        day = timezone.now().date()

    if request.user != lesson.teacher and not request.user.is_superuser:
        return HttpResponseForbidden("You are not authorized to set grades for this lesson.")

    # Fetch existing grades for the given date
    existing_grades = Grade.objects.filter(lesson=lesson, date_assigned=day)
    initial_data = {}
    if existing_grades.exists():
        max_grade = existing_grades.first().max_grade
        initial_data['max_grade'] = max_grade
        for grade in existing_grades:
            initial_data[f'grade_{grade.student.id}'] = grade.grade

    if request.method == 'POST':
        form = GradeForm(request.POST, request.FILES, students=students, initial=initial_data)
        if form.is_valid():
            form.save_grades(lesson, form.cleaned_data['date_assigned'], form.cleaned_data['file'])
            messages.success(request, "Grades successfully saved.")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
    else:
        form = GradeForm(students=students, initial=initial_data)

    return render(request, 'subjects/set_grade.html', {
        'form': form,
        'lesson': lesson,
        'students': students,
        'day': day
    })
@login_required
def grades_by_day_view(request):
    grades = Grade.objects.filter(student=request.user).select_related('lesson', 'lesson__teacher').order_by('date_assigned')

    # Group grades by date
    grades_by_date = {}
    for grade in grades:
        if grade.date_assigned not in grades_by_date:
            grades_by_date[grade.date_assigned] = []

        # Extract teacher information
        teacher = grade.lesson.teacher
        teacher_info = {
            'full_name': teacher.full_name if teacher else "No teacher assigned",
            'profile_picture': teacher.profile_picture.url if teacher and teacher.profile_picture else None
        }

        # Append the grade and teacher info
        grades_by_date[grade.date_assigned].append({
            'grade': grade,
            'teacher': teacher_info
        })

    return render(request, 'subjects/grades_by_day.html', {'grades_by_date': grades_by_date, 'page': 'diary'})

@login_required
def psy_appointment_view(request):
    week_offset = int(request.GET.get('week_offset', 0))  # Get the week offset from the request
    today = now().date()
    start_of_week = today - timedelta(days=today.weekday()) + timedelta(weeks=week_offset)
    dates_of_week = [start_of_week + timedelta(days=i) for i in range(7)]  # Get Monday to Sunday

    booked_appointments = Appointment.objects.filter(
        user=request.user, is_booked=True, date__gte=now().date(), type='psy'
    ).order_by('-date', '-start_time')

    if booked_appointments.exists():
        return redirect('appointments:success-appointment')

    context = {
        'dates_of_week': dates_of_week,
        'week_offset': week_offset,
    }
    return render(request, 'subjects/psy-appointment.html', context)

@login_required
def ori_appointment_view(request):
    booked_appointments = Appointment.objects.filter(
        user=request.user,
        is_booked=True,
        type='ori',
        date__gte=now().date()
    ).order_by('-date', '-start_time')

    if booked_appointments.exists():
        return redirect('appointments:success-appointment')

    today = now().date()
    start_of_week = today - timedelta(days=today.weekday())
    dates_of_week = [start_of_week + timedelta(days=i) for i in range(6)]

    context = {
        'dates_of_week': dates_of_week,
    }
    return render(request, 'subjects/ori-appointment.html', context)

@login_required
def create_volunteer_channel(request):
    form = VolunteerChannelForm(request.POST or None)
    search_form = UserSearchForm(request.GET or None)

    students = CustomUser.objects.filter(role='Student').order_by('full_name')[:8]

    if 'search' in request.GET and search_form.is_valid():
        search_query = request.GET.get('search', '')
        students = CustomUser.objects.filter(
            Q(full_name__icontains=search_query) | Q(phone_number__icontains(search_query)),
            role='Student'
        ).order_by('full_name')[:8]

    if request.method == 'POST':
        selected_students = request.POST.getlist('selected_students')
        if form.is_valid():
            volunteer_channel = form.save(commit=False)
            volunteer_channel.created_by = request.user  # Set the mentor who created the channel

            # Create the chat room
            chat_room = ChatRoom.objects.create(title=volunteer_channel.name)
            chat_room.participants.add(request.user)  # Add the creator to the chat room
            for student_id in selected_students:
                student = CustomUser.objects.get(id=student_id)
                chat_room.participants.add(student)

            volunteer_channel.chat_room = chat_room  # Associate the chat room with the channel
            volunteer_channel.save()
            volunteer_channel.users.set(selected_students)
            return redirect('subjects:volunteer_channel_list')
        else:
            print(form.errors)

    return render(request, 'subjects/volunteer_channel_form.html', {
        'form': form,
        'students': students,
        'page': 'channels',
        'search_form': search_form,
        'channels': VolunteerChannel.objects.all()
    })

#subjects/volunteer_channel_form.html
def search_users(request):
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        query = request.GET.get('term', '')
        users = CustomUser.objects.filter(role='Student')
        if query:
            users = users.filter(Q(full_name__icontains=query) | Q(phone_number__icontains=query))
        else:
            users = users.order_by('full_name')[:8]

        results = [{'id': user.id, 'label': user.full_name, 'value': user.full_name} for user in users]
        return JsonResponse(results, safe=False)
    return JsonResponse({'error': 'Not AJAX'}, status=400)

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .models import Lesson_crm2
from chats.models import ChatRoom, Message
from django.shortcuts import get_object_or_404
from django.utils.timezone import now
@csrf_exempt
@require_http_methods(["PATCH"])
def update_google_meet_link(request, lesson_id):
    lesson = get_object_or_404(Lesson_crm2, id=lesson_id)

    # Security check (ensure the user has permissions to update the lesson)
    if not (request.user.is_superuser or request.user == lesson.mentor):
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    try:
        data = json.loads(request.body)
        google_meet_link = data.get('link')
        if not google_meet_link:
            return JsonResponse({'error': 'No Google Meet link provided'}, status=400)

        # Update the lesson with the new Google Meet link
        lesson.google_meet_link = google_meet_link
        lesson.save()

        # Create a conference type message in the chat room
        Message.objects.create(
            chat_room=lesson.chat_room,
            user=request.user,
            message=google_meet_link,
            message_type='conf',
            timestamp=now()
        )

        return JsonResponse({'message': 'Google Meet link updated successfully'}, status=200)
    except json.JSONDecodeError as e:
        return JsonResponse({'error': f'Invalid JSON: {str(e)}'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def student_tasks_view(request):
    user = request.user
    if user.role != 'Student':
        return HttpResponseForbidden("You are not authorized to view this page.")

    # Get all lessons where the user is a student
    lessons = Lesson_crm2.objects.filter(group_template__students=user).select_related('teacher', 'subject', 'chat_room')
    tasks = Task.objects.filter(chat_room__in=[lesson.chat_room for lesson in lessons])
    student_tasks = Task.objects.filter(submissions__student=user)

    return render(request, 'subjects/student_tasks.html', {
        'tasks': tasks,
        'page': 'tasks',
        'lessons': lessons,
        'student_tasks': student_tasks,
        'file_upload_form': FileUploadForm()
    })

@login_required
def task_submissions_view(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    group_template = task.chat_room.lessons.first().group_template

    # Get all students in the group template associated with the task
    students = group_template.students.all()

    # Get all submissions for the specified task
    submissions = TaskSubmission.objects.filter(task=task).select_related('student')

    # Create a dictionary to map submissions to students
    submissions_dict = {submission.student.id: submission for submission in submissions}

    # Create a list to store students and their submissions status
    student_submissions = []
    for student in students:
        submission = submissions_dict.get(student.id, None)
        student_submissions.append({
            'student': student,
            'submission': submission
        })

    return render(request, 'subjects/task_submissions.html', {
        'task': task,
        'student_submissions': student_submissions
    })

@api_view(['POST'])
def upload_task_view(request):
    data = {
        'task': request.data.get('task_id'),
        'student': request.user.id,
        'file': request.FILES.get('file')
    }
    serializer = TaskSubmissionSerializer(data=data)
    if serializer.is_valid():
        serializer.save()
        return Response({'success': True}, status=status.HTTP_200_OK)
    return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

@login_required
def download_task_file(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    if not task.file:
        return JsonResponse({'error': 'File not found'}, status=404)

    response = FileResponse(task.file.open(), as_attachment=True, filename=task.file.name)
    return response

@login_required
def download_submission_file(request, submission_id):
    submission = get_object_or_404(TaskSubmission, id=submission_id)
    if not submission.file:
        return JsonResponse({'error': 'File not found'}, status=404)

    response = FileResponse(submission.file.open(), as_attachment=True, filename=submission.file.name)
    return response


@login_required
def download_grade_file(request, grade_id):
    grade = get_object_or_404(Grade, id=grade_id)
    if not grade.file:
        return JsonResponse({'error': 'File not found'}, status=404)

    response = FileResponse(grade.file.open(), as_attachment=True, filename=grade.file.name)
    return response


from django.contrib.auth import get_user_model

User = get_user_model()

def create_achievement(request):
    achievement_form = AchievementForm(request.POST or None)
    students = User.objects.filter(role='Student')

    if request.method == 'POST':
        if achievement_form.is_valid():
            achievement = achievement_form.save()
            students_ids = request.POST.getlist('selected_students')
            successes = 0
            errors = []

            for student_id in students_ids:
                student_achievement_form = StudentAchievementForm(data={
                    'student': student_id,
                    'achievement': achievement.id
                })

                if student_achievement_form.is_valid():
                    student_achievement_form.save()
                    successes += 1
                else:
                    errors.append(student_achievement_form.errors)
                    messages.error(request, f"Error creating Student Achievement for student ID {student_id}")

            if successes:
                messages.success(request, f"{successes} Student Achievements successfully created!")
            else:
                messages.error(request, "Failed to create any Student Achievements.")

            return redirect('subjects:set_achievement')

    context = {
        'achievement_form': achievement_form,
        'students': students,
        'page': 'achievements',
        'errors': errors if 'errors' in locals() else [],
    }
    return render(request, 'subjects/set_achievement.html', context)

#subjects:set_achievement

@login_required
def achievements_list(request):
    total_achievements = Achievement.objects.count()
    user_achievements = StudentAchievement.objects.filter(student=request.user).count()

    if total_achievements > 0:
        achievement_percentage = (user_achievements / total_achievements) * 100
    else:
        achievement_percentage = 0

    achievements = StudentAchievement.objects.select_related('achievement').filter(student=request.user)

    # Initialize counts
    counts = {'diamond': 0, 'gold': 0, 'iron': 0}

    # Count achievements based on difficulty
    for achievement in achievements:
        if achievement.achievement.difficulty == 5:
            counts['diamond'] += 1
        elif 3 <= achievement.achievement.difficulty <= 4:
            counts['gold'] += 1
        elif 1 <= achievement.achievement.difficulty <= 2:
            counts['iron'] += 1

    context = {
        'achievements': achievements,
        'page': 'achievements',
        'counts': counts,
        'achievement_percentage': achievement_percentage
    }
    return render(request, 'subjects/achievements_list.html', context)
