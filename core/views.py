from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView


class HomePageView(LoginRequiredMixin, TemplateView):
    login_url = "/users/login/"
    template_name = 'core/home.html'


class WelcomePageView(TemplateView):
    template_name = 'core/welcome.html'
