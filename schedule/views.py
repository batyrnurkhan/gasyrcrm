from django.views.generic import CreateView, UpdateView
from django.http import HttpResponseForbidden


from django.shortcuts import render
from .models import Shift

def shifts_view(request):
    # This will fetch all shifts and their associated times and lessons
    shifts = Shift.objects.prefetch_related('times__lessons').all()
    return render(request, 'schedule/shifts.html', {'shifts': shifts})
