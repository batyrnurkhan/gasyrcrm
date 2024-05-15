import random
import re
import logging

from django.contrib import messages
from django.contrib.auth import authenticate, login, get_user_model, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse
from django.shortcuts import render, redirect
from django.views.generic import TemplateView, View
from users.forms import CustomUserAuthenticationForm, AccessCodeForm, ProfileUpdateForm, PasswordChangeForm, \
    TeacherCreationForm
from users.models import CustomUser

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
        login_code = generate_unique_code()  # Generate the login code here

        # Create the user instance with all necessary data
        user = CustomUser.objects.create_user(
            phone_number=phone_number,
            password=password,
            full_name=full_name,
            user_city=user_city,
            login_code=login_code  # Set login code for the user instance
        )
        return redirect('users:login')


class ShowCodeView(LoginRequiredMixin, TemplateView):
    template_name = 'users/show_code.html'

    def get(self, request, *args, **kwargs):
        # Redirect teachers and superusers directly to the home page
        if request.user.is_superuser or request.user.role == 'Teacher' or request.user.has_access:
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
            formatted_phone_number = re.sub(r'\D', '', raw_phone_number)  # Strip non-numeric characters
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=formatted_phone_number, password=password)

            if user is not None:
                login(request, user)
                if user.has_access or user.role in ['Teacher', 'Superuser']:
                    redirect_url = request.GET.get("next", "/home/")
                    return redirect(redirect_url)  # Redirect to a home page or dashboard suitable for privileged users
                else:
                    return redirect('users:show_code')  # Redirect to the page where users can see their access code
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


class ProfileView(LoginRequiredMixin, View):
    form_class = ProfileUpdateForm
    template_name = 'users/profile.html'

    def get(self, request):
        form = self.form_class(instance=request.user, user=request.user)
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = self.form_class(request.POST, request.FILES, instance=request.user, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('users:profile')  # Redirect to the same profile page or a confirmation page
        messages.error(request, 'Form is invalid')
        return render(request, self.template_name, {'form': form})


@login_required
def change_password(request):
    form = PasswordChangeForm(request.POST)
    if form.is_valid():
        old_password = form.cleaned_data.get('old_password')
        new_password = form.cleaned_data.get('new_password')
        user = request.user
        if user.check_password(old_password):
            user.set_password(new_password)
            user.save()
            update_session_auth_hash(request, user)  # Important!
            messages.success(request, 'Ваш пароль был успешно обновлен!')
        else:
            messages.error(request, "Неправильный пароль")
    else:
        messages.error(request, form.errors)
    return redirect('users:profile')  # Redirect to the same profile page or a confirmation page


class CheckAccessView(LoginRequiredMixin, View):
    def post(self, request):
        if request.user.has_access:
            return JsonResponse({'has_access': True, 'url': reverse('home')})
        else:
            return JsonResponse({'has_access': False, 'message': 'Администратор еще не подтвердил ваш аккаунт.'})


def log_out(request):
    logout(request)
    return redirect("users:login")


@login_required
def create_teacher(request):
    if not (request.user.is_superuser or request.user.role == 'Mentor'):
        messages.error(request, "Unauthorized access.")
        return redirect('home')

    if request.method == 'POST':
        form = TeacherCreationForm(request.POST)
        if form.is_valid():
            user, password = form.save()  # Save the user and get the generated password
            # Pass the details to the template directly
            context = {
                'form': TeacherCreationForm(),  # Reset the form for new input
                'created': True,
                'user_phone': user.phone_number,
                'user_password': password
            }
            return render(request, 'users/create_teacher.html', context)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = TeacherCreationForm()

    return render(request, 'users/create_teacher.html', {'form': form})