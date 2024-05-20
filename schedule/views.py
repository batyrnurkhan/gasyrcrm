from django.contrib.auth.decorators import login_required
from django.views.generic import CreateView, UpdateView
from django.http import HttpResponseForbidden


from django.shortcuts import render
from .models import Shift

def shifts_view(request):
    shifts = Shift.objects.prefetch_related(
        'times__lessons',
        'times__lessons__teacher'
    ).all()

    if not shifts:
        print("No shifts found.")
    else:
        print(f"Found {len(shifts)} shifts.")

    return render(request, 'schedule/shifts.html', {'shifts': shifts})