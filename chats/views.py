from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required

from subjects.models import Lesson_crm2, VolunteerChannel
from .models import ChatRoom
from .forms import MessageForm

def chat_room_list(request):
    rooms = ChatRoom.objects.all()
    return render(request, 'chats/chat_room_list.html', {'rooms': rooms})


#### НАДО ПОДУМАТЬ ####
@login_required
def chat_room_detail(request, room_id):
    room = get_object_or_404(ChatRoom, id=room_id)
    volunteer_channel = VolunteerChannel.objects.filter(chat_room=room).first()
    if volunteer_channel:
        template_name = 'chats/chat_room_detail_volunteer.html'
    else:
        template_name = 'chats/chat_room_detail_subjects.html'

    # Checking lesson and permissions logic
    try:
        lesson = Lesson_crm2.objects.get(chat_room=room)
        students = lesson.students.all()
        teacher = lesson.teacher

        # Check if the logged-in user is the teacher, mentor, superuser, or a student of the lesson
        if not (request.user.is_superuser or request.user == lesson.mentor or request.user == lesson.teacher or request.user in students):
            return HttpResponseForbidden("You are not allowed to view this chat room.")
    except ObjectDoesNotExist:
        lesson = None
        students = []
        teacher = None

    # Handling messages
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.chat_room = room
            message.user = request.user
            message.save()
            return redirect('chats:chat_room_detail', room_id=room_id)
    else:
        form = MessageForm()

    messages = room.messages.all().order_by('-timestamp')
    context = {
        'room': room,
        'all_messages': messages,
        'lesson': lesson,
        'form': form,
        'group_template_users': students,
        'teacher': teacher,
        'volunteer_channel': volunteer_channel
    }
    return render(request, template_name, context)