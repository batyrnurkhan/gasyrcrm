from django.db import transaction
from rest_framework import generics, permissions

from chats.models import ChatRoom
from .models import Subject, GroupTemplate, Lesson_crm2
from .permissions import IsMentorSuperuserOrGroupMember
from .serializers import SubjectSerializer, GroupTemplateSerializer, LessonSerializer

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
