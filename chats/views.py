from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required

from subjects.models import Lesson_crm2
from .models import ChatRoom
from .forms import MessageForm

def chat_room_list(request):
    rooms = ChatRoom.objects.all()
    return render(request, 'chats/chat_room_list.html', {'rooms': rooms})


@login_required
def chat_room_detail(request, room_id):
    room = get_object_or_404(ChatRoom, id=room_id)
    try:
        lesson = Lesson_crm2.objects.get(chat_room=room)
        group_template_users = lesson.group_template.students.all()
        teacher = lesson.teacher

        if not (request.user.is_superuser or request.user == lesson.mentor or request.user in group_template_users):
            return HttpResponseForbidden("You are not allowed to view this chat room.")
    except ObjectDoesNotExist:
        # Handle the case where there is no lesson linked to this chat room
        lesson = None
        group_template_users = []
        teacher = None

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
    return render(request, 'chats/chat_room_detail_subjects.html', {
        'room': room,
        'messages': messages,
        'lesson': lesson,
        'form': form,
        'group_template_users': group_template_users,
        'teacher': teacher
    })