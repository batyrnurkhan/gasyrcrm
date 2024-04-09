from django.urls import path
from .views import SignUpView, CustomLoginView, ShowCodeView

app_name = 'users'

urlpatterns = [
    path('signup/', SignUpView.as_view(), name='signup'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('show_code/', ShowCodeView.as_view(), name='show_code'),
]
