from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from .models import ChatRoom
from .forms import MessageForm

def chat_room_list(request):
    rooms = ChatRoom.objects.all()
    return render(request, 'chats/chat_room_list.html', {'rooms': rooms})

def chat_room_detail(request, room_id):
    room = get_object_or_404(ChatRoom, id=room_id)
    return render(request, 'chats/chat_room_detail.html', {'room': room})


@login_required
def chat_room_detail(request, room_id):
    room = get_object_or_404(ChatRoom, id=room_id)
    if request.method == 'POST':
        form = MessageForm(request.POST, request.FILES)  # Include request.FILES for file data
        if form.is_valid():
            message = form.save(commit=False)
            message.chat_room = room
            message.user = request.user
            if message.message or message.file:  # Ensure either message or file is present
                message.save()
            return redirect('chats:chat_room_detail', room_id=room_id)
    else:
        form = MessageForm()

    messages = room.messages.all().order_by('-timestamp')  # Optionally order messages
    return render(request, 'chats/chat_room_detail.html', {
        'room': room,
        'messages': messages,
        'form': form
    })