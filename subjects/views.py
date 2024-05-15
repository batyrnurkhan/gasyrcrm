from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView
from rest_framework import generics, permissions
from rest_framework.generics import get_object_or_404

from chats.models import ChatRoom, Message
from users.models import CustomUser
from .forms import TaskForm, LessonForm, GroupTemplateForm, UserSearchForm
from .models import Subject, GroupTemplate, Lesson_crm2, Task
from .permissions import IsMentorSuperuserOrGroupMember
from .serializers import SubjectSerializer, GroupTemplateSerializer, LessonSerializer, TaskSerializer


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


class LessonListView(CreateView):
    model = Lesson_crm2
    form_class = LessonForm
    template_name = 'subjects/lesson_create.html'
    success_url = reverse_lazy('lesson_list')  # Adjust this to the correct URL for listing lessons

    def form_valid(self, form):
        with transaction.atomic():
            chat_room = ChatRoom.objects.create(title="Temporary Title")  # Initial title
            self.object = form.save(commit=False)
            self.object.mentor = self.request.user  # Automatically set mentor to the current user
            self.object.save()
            chat_room.title = f"Lesson {self.object.id} Chat"
            chat_room.save()

            # Add users to chat room
            for student in self.object.group_template.students.all():
                chat_room.participants.add(student)
            if self.object.teacher:
                chat_room.participants.add(self.object.teacher)
            return super().form_valid(form)

from rest_framework import generics

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

    student_list = list(students.values('id', 'full_name'))  # Create a list of dicts
    return JsonResponse(student_list, safe=False)