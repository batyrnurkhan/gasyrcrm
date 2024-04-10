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


class CustomLoginView(LoginView):
    template_name = 'users/login.html'
    form_class = CustomUserAuthenticationForm

    def form_valid(self, form):
        username = form.cleaned_data.get('username')  # Adjust based on your form field
        password = form.cleaned_data.get('password')

        user = authenticate(self.request, username=username, password=password)
        print("Authenticated user:", user)
        if user is not None:
            login(self.request, user)

            if user.role == 'Teacher' or user.is_superuser:
                return redirect('core:home')

            user.login_code = generate_unique_code()
            user.save()
            return HttpResponseRedirect(reverse('users:show_code'))
        else:
            # Handle the case where authentication fails
            return super().form_invalid(form)

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            # Print form errors to the console or log them
            print(form.errors)
            return self.form_invalid(form)

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
                login(request, user)
                # Check if the user is a teacher, superuser, or any other role that should redirect to home
                if user.role == 'Teacher' or user.is_superuser:
                    return redirect('home')  # Replace 'home_page' with the name of your actual home page URL
                else:
                    return redirect('users:show_code')  # Redirect to the specific page for other roles
            else:
                form.add_error(None, "Phone number or password is incorrect.")
    else:
        form = CustomUserAuthenticationForm()

    return render(request, 'users/login.html', {'form': form})