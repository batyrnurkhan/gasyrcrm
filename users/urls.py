from django.urls import path
from .views import SignUpView, CustomLoginView, ShowCodeView, login_view

app_name = 'users'

urlpatterns = [
    path('signup/', SignUpView.as_view(), name='signup'),
    path('login/', login_view, name='login'),
    path('show_code/', ShowCodeView.as_view(), name='show_code'),
]
