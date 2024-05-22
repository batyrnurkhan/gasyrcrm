from django.contrib.auth.decorators import login_required
from django.views.generic import CreateView, UpdateView
from django.http import HttpResponseForbidden


from django.shortcuts import render
from .models import Shift

def shifts_view(request):
    # Fetch all shifts and related data in an optimized manner
    shifts = Shift.objects.prefetch_related(
        'times__lessons',
        'times__lessons__teacher',
        'times__lessons__subject',
        'times__lessons__group_template'
    ).all()

    if not shifts:
        print("No shifts found.")
    else:
        print(f"Found {len(shifts)} shifts.")

    return render(request, 'schedule/shifts.html', {'shifts': shifts})