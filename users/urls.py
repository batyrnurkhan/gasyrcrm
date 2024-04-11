from django.urls import path
from .views import SignUpView, ShowCodeView, login_view, grant_access_view

app_name = 'users'

urlpatterns = [
    path('signup/', SignUpView.as_view(), name='signup'),
    path('login/', login_view, name='login'),
    path('show_code/', ShowCodeView.as_view(), name='show_code'),
    path('grant-access/', grant_access_view, name='grant_access'),

]
