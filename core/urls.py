"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

from core.views import HomePageView, WelcomePageView, MyCoursesPageView, CompletedCoursesPageView, CoursePageView

app_name = 'core'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('users/', include('users.urls')),
    path('courses/', include('courses.urls')),
    path('appointments/', include('appointments.urls')),
    path('chats/', include('chats.urls')),
    path('subjects/', include('subjects.urls')),
    path('schedule/', include('schedule.urls')),
    path('news/', include('news.urls')),

    path('ckeditor/', include('ckeditor_uploader.urls')),

    path('', WelcomePageView.as_view(), name='welcome'),
    path('home/', HomePageView.as_view(), name='home'),
    path('my-courses/', MyCoursesPageView.as_view(), name='my-courses'),
    path('completed-courses/', CompletedCoursesPageView.as_view(), name='completed-courses'),
    

]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
