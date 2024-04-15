from django.urls import path
from .views import SignUpView, ShowCodeView, LoginView, GrantAccessView, ProfileView

app_name = 'users'

urlpatterns = [
    path('signup/', SignUpView.as_view(), name='signup'),
    path('login/', LoginView.as_view(), name='login'),
    path('show_code/', ShowCodeView.as_view(), name='show_code'),  # Ensure this is correct
    path('grant-access/', GrantAccessView.as_view(), name='grant_access'),
    path('profile/', ProfileView.as_view(), name='profile'),

]
