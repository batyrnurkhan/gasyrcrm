from django.urls import path
from .views import SignUpView, ShowCodeView, LoginView, GrantAccessView, ProfileView, CheckAccessView, log_out, \
    change_password

app_name = 'users'

urlpatterns = [
    path('signup/', SignUpView.as_view(), name='signup'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', log_out, name='logout'),
    path('show_code/', ShowCodeView.as_view(), name='show_code'),  # Ensure this is correct
    path('grant-access/', GrantAccessView.as_view(), name='grant_access'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('check-access/', CheckAccessView.as_view(), name='check-access'),
    path('change-password/', change_password, name='change_password'),

]
