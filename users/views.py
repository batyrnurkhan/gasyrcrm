from django.contrib.auth import get_user_model
from django.views.generic import CreateView, TemplateView
from django.urls import reverse_lazy, reverse
from users.forms import CustomUserCreationForm
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

    def post(self, request, *args, **kwargs):
        phone_number = request.POST.get('phone_number')
        password = request.POST.get('password')
        user = authenticate(request, username=phone_number, password=password)
        if user is not None:
            login(request, user)
            # Generate and save the login code as before
            user.login_code = generate_unique_code()
            user.save()
            # Redirect to the 'show_code' page
            return HttpResponseRedirect(reverse('users:show_code'))
        else:
            return self.form_invalid(form)


class ShowCodeView(LoginRequiredMixin, TemplateView):
    template_name = 'users/show_code.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['login_code'] = self.request.user.login_code
        return context