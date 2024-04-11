from django.contrib.auth import get_user_model
from django.views.generic import CreateView, TemplateView
from django.urls import reverse_lazy, reverse
from users.forms import CustomUserCreationForm, CustomUserAuthenticationForm
import random
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect, render
from django.http import HttpResponseRedirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.contrib.auth import authenticate, login
class SignUpView(View):
    def get(self, request):
        return render(request, 'users/signup.html')

    def post(self, request):
        # Extract the data from the request
        full_name = request.POST.get('full_name')
        phone_number = request.POST.get('phone_number')
        user_city = request.POST.get('user_city')
        password = request.POST.get('password')

        CustomUser = get_user_model()
        user = CustomUser.objects.create_user(
            phone_number=phone_number,
            password=password,
            full_name=full_name,
            user_city=user_city
        )

        return redirect('users:login')


def generate_unique_code():
    return "{:03d}-{:03d}".format(random.randint(0, 999), random.randint(0, 999))

import logging

logger = logging.getLogger(__name__)

class ShowCodeView(LoginRequiredMixin, TemplateView):
    template_name = 'users/show_code.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['login_code'] = self.request.user.login_code
        return context

import re
def login_view(request):
    if request.method == "POST":
        form = CustomUserAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            raw_phone_number = form.cleaned_data.get('phone_number')
            formatted_phone_number = re.sub(r'\D', '', raw_phone_number)
            password = form.cleaned_data.get('password')

            user = authenticate(request, username=formatted_phone_number, password=password)
            if user is not None:
                if not user.login_code:
                    user.login_code = "{:03d}-{:03d}".format(random.randint(0, 999), random.randint(0, 999))
                    user.save()

                login(request, user)
                # Redirect based on user's access level or role
                if user.role in ['Teacher', 'Superuser'] or user.has_access:
                    return redirect('home')  # Adjust this to your home page's name
                else:
                    return HttpResponseRedirect(reverse('users:show_code'))
            else:
                form.add_error(None, "Phone number or password is incorrect.")
    else:
        form = CustomUserAuthenticationForm()

    return render(request, 'users/login.html', {'form': form})


from django.shortcuts import render, redirect
from .forms import AccessCodeForm

def grant_access_view(request):
    user_info = None  # Initialize variable to hold user information
    form = AccessCodeForm(request.POST or None)  # Handle form submission and initial GET request

    if request.method == 'POST' and form.is_valid():
        login_code = form.cleaned_data.get('login_code')
        CustomUser = get_user_model()

        try:
            user_to_grant = CustomUser.objects.get(login_code=login_code)
            # Update the user's has_access field only if it's a POST request meant to update the access
            if 'grant_access' in request.POST:
                user_to_grant.has_access = True
                user_to_grant.save()
                # Redirect or notify the user of success
            # Regardless of POST intent, load the user's info to display
            user_info = {
                'full_name': user_to_grant.full_name,
                'phone_number': user_to_grant.phone_number,
                'user_city': user_to_grant.user_city,
                'has_access': user_to_grant.has_access,
            }
        except CustomUser.DoesNotExist:
            form.add_error('login_code', 'No user found with this login code.')

    return render(request, 'users/grant_access.html', {'form': form, 'user_info': user_info})