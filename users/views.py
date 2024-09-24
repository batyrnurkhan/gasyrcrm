import random
import re
import logging

from django.contrib import messages
from django.contrib.auth import authenticate, login, get_user_model, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView, View, DetailView
from django.views.generic.edit import FormMixin

from users.forms import CustomUserAuthenticationForm, AccessCodeForm, ProfileUpdateForm, PasswordChangeForm, \
    TeacherCreationForm, StudentProfileForm
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
            return redirect('courses:home')
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
        if form.is_valid():
            login_code = form.cleaned_data['login_code']
            try:
                user = get_user_model().objects.get(login_code=login_code)
                if 'grant_access' in request.POST:
                    user.has_access = True
                    user.role = "Student"
                    user.save()
                user_data = {
                    'full_name': user.full_name,
                    'phone_number': user.phone_number,
                    'user_city': user.user_city,
                    'has_access': user.has_access,
                    'login_code': user.login_code,
                }
                return JsonResponse({'status': 'success', 'user': user_data}, status=200)
            except get_user_model().DoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'Нет такого пользователя с такким кодом'}, status=404)
        else:
            return JsonResponse({'status': 'error', 'message': 'Неправильные данные'}, status=400)


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
            messages.success(request, 'Профиль успешно обновлен')
            return redirect('users:profile')  # Redirect to the same profile page or a confirmation page
        messages.error(request, 'Неправильно заполнены данные')
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
    return redirect('users:profile')


class CheckAccessView(LoginRequiredMixin, View):
    def post(self, request):
        if request.user.has_access:
            return JsonResponse({'has_access': True, 'url': reverse('subjects:home')})
        else:
            return JsonResponse({'has_access': False, 'message': 'Администратор еще не подтвердил ваш аккаунт.'})


def log_out(request):
    logout(request)
    return redirect("users:login")


@login_required
def create_teacher(request):
    if not (request.user.is_superuser or request.user.role == 'Mentor'):
        messages.error(request, "Неавторизованный")
        return redirect('subjects:home')

    if request.method == 'POST':
        form = TeacherCreationForm(request.POST)
        if form.is_valid():
            user, password = form.save()  # Save the user and get the generated password
            # Store the password temporarily in the session using phone_number
            request.session[user.phone_number] = password
            success_message = f'Учитель успешно создан!'
            messages.success(request, success_message)
            response = redirect('users:create-teacher')
            response['Location'] += f'?phone={user.phone_number}'
            return response
        else:
            messages.error(request, 'Пожалуйста убедитесь что ввели правильно')
    else:
        form = TeacherCreationForm()

    teachers = CustomUser.objects.filter(role='Teacher')
    passwords = {teacher.phone_number: request.session.get(teacher.phone_number) for teacher in teachers}
    context = {
        'form': form,
        'teachers': teachers,
        'passwords': passwords,
        'page': 'teachers',
    }
    phone = request.GET.get('phone')
    if phone: context['phone'] = phone
    return render(request, 'users/create_teacher.html', context)



class StudentCheckProfileView(LoginRequiredMixin, DetailView):
    model = CustomUser
    template_name = 'users/student_check_profile.html'
    context_object_name = 'student'

    def post(self, request, *args, **kwargs):
        student = self.get_object()
        # Get data from the request
        admission_country = request.POST.get('admission_country')
        education_class = request.POST.get('education_class')

        try:
            # Update the student object
            if admission_country is not None:
                student.admission_country = admission_country
            if education_class is not None:
                student.education_class = education_class

            student.save()

            return JsonResponse({'success': True, 'message': 'Changes saved successfully!'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': 'An error occurred while saving changes.'})