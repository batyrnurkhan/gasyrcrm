import random
import re
import logging
from django.contrib.auth import authenticate, login, get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.shortcuts import render, redirect
from django.views.generic import TemplateView, View
from users.forms import CustomUserAuthenticationForm, AccessCodeForm

logger = logging.getLogger(__name__)
def generate_unique_code():
    CustomUser = get_user_model()

    while True:
        potential_code = "{:03d}-{:03d}".format(random.randint(0, 999), random.randint(0, 999))
        if not CustomUser.objects.filter(login_code=potential_code).exists():
            return potential_code

class SignUpView(View):
    def get(self, request):
        return render(request, 'users/signup.html')

    def post(self, request):
        full_name = request.POST.get('full_name')
        phone_number = request.POST.get('phone_number')
        user_city = request.POST.get('user_city')
        password = request.POST.get('password')
        CustomUser = get_user_model()
        CustomUser.objects.create_user(
            phone_number=phone_number,
            password=password,
            full_name=full_name,
            user_city=user_city
        )
        return redirect('users:login')

class ShowCodeView(LoginRequiredMixin, TemplateView):
    template_name = 'users/show_code.html'

    def get(self, request, *args, **kwargs):
        if request.user.is_superuser or request.user.role == 'Teacher':
            return redirect('home')
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['login_code'] = self.request.user.login_code
        return context

class LoginView(View):
    form_class = CustomUserAuthenticationForm

    def get(self, request):
        form = self.form_class()
        return render(request, 'users/login.html', {'form': form})

    def post(self, request):
        form = self.form_class(request, data=request.POST)
        if form.is_valid():
            raw_phone_number = form.cleaned_data.get('phone_number')
            formatted_phone_number = re.sub(r'\D', '', raw_phone_number)
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=formatted_phone_number, password=password)
            if user:
                if not user.login_code:
                    user.login_code = generate_unique_code()
                    user.save()
                login(request, user)
                if user.role in ['Teacher', 'Superuser'] or user.has_access:
                    return redirect('home')  # Adjust this to your home page's name
                else:
                    return HttpResponseRedirect(reverse('users:show_code'))
            else:
                form.add_error(None, "Phone number or password is incorrect.")
        return render(request, 'users/login.html', {'form': form})

class GrantAccessView(View):
    form_class = AccessCodeForm

    def get(self, request):
        form = self.form_class()
        return render(request, 'users/grant_access.html', {'form': form})

    def post(self, request):
        form = self.form_class(request.POST)
        user_info = None
        if form.is_valid():
            login_code = form.cleaned_data.get('login_code')
            CustomUser = get_user_model()
            try:
                user_to_grant = CustomUser.objects.get(login_code=login_code)
                if 'grant_access' in request.POST:
                    user_to_grant.has_access = True
                    user_to_grant.save()
                user_info = {
                    'full_name': user_to_grant.full_name,
                    'phone_number': user_to_grant.phone_number,
                    'user_city': user_to_grant.user_city,
                    'has_access': user_to_grant.has_access,
                }
            except CustomUser.DoesNotExist:
                form.add_error('login_code', 'No user found with this login code.')
        return render(request, 'users/grant_access.html', {'form': form, 'user_info': user_info})