from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.generic import ListView, DetailView, CreateView
from rest_framework.generics import get_object_or_404
from chats.models import ChatRoom, Message
from users.models import CustomUser
from .forms import TaskForm, LessonForm, GroupTemplateForm, UserSearchForm, VolunteerChannelForm, GradeForm
from .models import Subject, GroupTemplate, Lesson_crm2, Task, VolunteerChannel


class SubjectListView(ListView):
    model = Subject
    template_name = 'subjects/subject_list.html'

def group_template_list(request):
    form = GroupTemplateForm(request.POST or None)
    search_form = UserSearchForm(request.GET or None)
    students = []
    group_templates = GroupTemplate.objects.all()  # Fetch all group templates

    if 'search' in request.GET and search_form.is_valid():
        students = search_form.search_users()

    if request.method == 'POST' and 'create_template' in request.POST:
        if form.is_valid():
            group_template = form.save(commit=False)
            selected_students = request.POST.getlist('selected_students')
            group_template.save()
            group_template.students.set(selected_students)  # Save selected students to the group template
            return redirect('subjects:grouptemplate-list')  # Redirect to avoid double POST on refresh

    return render(request, 'subjects/group_template_list.html', {
        'form': form,
        'search_form': search_form,
        'students': students,
        'group_templates': group_templates  # Pass the list of group templates to the template
    })


class LessonCreateView(CreateView):
    model = Lesson_crm2
    form_class = LessonForm
    template_name = 'subjects/lesson_create.html'

    def get_context_data(self, **kwargs):
        # Ensure the time_id is passed to the template for the hidden field
        context = super().get_context_data(**kwargs)
        context['time_id'] = self.kwargs['time_id']
        return context

    def get_success_url(self):
        # Redirects back to the shifts page after successful creation
        return reverse('schedule:shifts')

    def form_valid(self, form):
        # This method is called when valid form data has been POSTed.
        # It should return an HttpResponse.
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

class LessonDetailView(DetailView):
    model = Lesson_crm2
    template_name = 'subjects/lesson_detail.html'

    def get_object(self):
        lesson = super().get_object()
        # Optionally, check permissions here
        return lesson

from django.utils.timezone import localtime

def create_task(request, room_id):
    room = get_object_or_404(ChatRoom, id=room_id)
    if request.method == 'POST':
        form = TaskForm(request.POST, request.FILES)
        if form.is_valid():
            task = form.save(commit=False)
            task.chat_room = room
            task.created_by = request.user
            task.save()

            # After saving the task, also create a message in the chat
            message_content = f"Задание от учителя: {task.name} - {localtime(task.deadline).strftime('%Y-%m-%d %H:%M')}"
            if task.file:
                message_content += f" <a href='{task.file.url}'>Download</a>"

            Message.objects.create(
                chat_room=room,
                user=request.user,  # or a system user if you have one
                message=message_content
            )

            return redirect('chats:chat_room_detail', room_id=room_id)  # Adjust this to your chat detail view
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
def create_volunteer_channel(request):
    if not (request.user.role == 'Mentor' or request.user.is_superuser):
        messages.error(request, "Only mentors and superusers can create channels.")
        return redirect('home')

    if request.method == 'POST':
        form = VolunteerChannelForm(request.POST, request.FILES)
        if form.is_valid():
            volunteer_channel = form.save(commit=False)
            chat_room = ChatRoom.objects.create(title=f"Chat for {volunteer_channel.name}")
            volunteer_channel.chat_room = chat_room  # Ensure this assignment is done correctly
            volunteer_channel.save()
            form.save_m2m()
            for user in volunteer_channel.users.all():
                chat_room.participants.add(user)
            chat_room.participants.add(request.user)  # Optionally adding the creator
            return redirect('subjects:volunteer_channel_list')
    else:
        form = VolunteerChannelForm()

    return render(request, 'subjects/volunteer_channel_form.html', {'form': form})


def volunteer_channel_list(request):
    channels = VolunteerChannel.objects.all()
    return render(request, 'subjects/volunteer_channel_list.html', {'channels': channels})


@login_required
def set_grade(request, lesson_id):
    lesson = get_object_or_404(Lesson_crm2, id=lesson_id)
    students = lesson.group_template.students.all()
    if request.user != lesson.teacher and not request.user.is_superuser:
        return HttpResponseForbidden("You are not authorized to set grades for this lesson.")

    if request.method == 'POST':
        form = GradeForm(request.POST, students=students)
        if form.is_valid():
            form.save_grades(lesson, form.cleaned_data['date_assigned'])
    else:
        form = GradeForm(students=students)

    return render(request, 'subjects/set_grade.html', {
        'form': form,
        'lesson': lesson,
        'students': students
    })