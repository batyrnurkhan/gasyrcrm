from django.db import transaction
from django.shortcuts import redirect, render
from rest_framework import generics, permissions
from rest_framework.generics import get_object_or_404

from chats.models import ChatRoom, Message
from .forms import TaskForm
from .models import Subject, GroupTemplate, Lesson_crm2, Task
from .permissions import IsMentorSuperuserOrGroupMember
from .serializers import SubjectSerializer, GroupTemplateSerializer, LessonSerializer, TaskSerializer


class SubjectListView(generics.ListCreateAPIView):
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer
    permission_classes = [permissions.IsAuthenticated]

class GroupTemplateListView(generics.ListCreateAPIView):
    queryset = GroupTemplate.objects.all()
    serializer_class = GroupTemplateSerializer
    permission_classes = [permissions.IsAuthenticated]


class LessonListView(generics.ListCreateAPIView):
    queryset = Lesson_crm2.objects.all()
    serializer_class = LessonSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        if not (self.request.user.role == 'Mentor' or self.request.user.is_superuser):
            raise permissions.PermissionDenied("You do not have permission to create a lesson.")

        with transaction.atomic():  # Ensures that both Lesson and ChatRoom are created successfully
            lesson = serializer.save(mentor=self.request.user)

            # Create a ChatRoom
            chat_room = ChatRoom.objects.create(title=f"Lesson {lesson.id} Chat")
            # Add all users from the selected group template to the chat room
            for student in lesson.group_template.students.all():
                chat_room.participants.add(student)
            chat_room.participants.add(lesson.teacher)  # Add the teacher as well
            chat_room.save()

from rest_framework import generics

class LessonDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Lesson_crm2.objects.all()
    serializer_class = LessonSerializer
    permission_classes = [IsMentorSuperuserOrGroupMember]

    def get_object(self):
        obj = super().get_object()
        self.check_object_permissions(self.request, obj)
        return obj

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