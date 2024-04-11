from django.shortcuts import render, redirect
from django.views.generic import ListView, DetailView

from .forms import CourseForm, ModuleForm, LessonForm, CourseFormStep2, CourseFormStep1
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView

from .models import Module, Lesson, Course


def create_course_step1(request):
    if request.method == 'POST':
        form = CourseFormStep1(request.POST, request.FILES)
        if form.is_valid():
            # Save non-file fields in session
            course_step1_data = form.cleaned_data
            # Exclude the file field from what's stored in the session
            course_step1_data.pop('course_picture', None)
            request.session['course_step1_data'] = course_step1_data
            # Handle the file upload here or in the final step

            return redirect('courses:create_course_step2')
    else:
        form = CourseFormStep1()
    return render(request, 'courses/create_course_step1.html', {'form': form})

def create_course_step2(request):
    if request.method == 'POST':
        form = CourseFormStep2(request.POST)
        if form.is_valid():
            course_data = request.session.get('course_step1_data', {})
            course = Course(**course_data, **form.cleaned_data)
            course.created_by = request.user
            course.save()
            # Clear the session data
            del request.session['course_step1_data']
            return redirect('courses:course_detail', pk=course.pk)
    else:
        form = CourseFormStep2()
    return render(request, 'courses/create_course_step2.html', {'form': form})

class CourseListView(ListView):
    model = Course
    context_object_name = 'courses'
    template_name = 'courses/course_list.html'

class CourseDetailView(DetailView):
    model = Course
    context_object_name = 'course'
    template_name = 'courses/course_detail.html'

def create_course(request):
    if request.method == 'POST':
        form = CourseForm(request.POST, request.FILES)
        if form.is_valid():
            course = form.save(commit=False)
            course.created_by = request.user
            course.save()
            return redirect('courses:course_detail', pk=course.pk)
    else:
        form = CourseForm()
    return render(request, 'courses/create_course.html', {'form': form})


class ModuleDetailView(DetailView):
    model = Module
    context_object_name = 'module'
    template_name = 'courses/module_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Additional context data can be added here if needed
        return context

class ModuleCreateView(CreateView):
    model = Module
    form_class = ModuleForm
    template_name = 'courses/module_form.html'
    # Assuming you have a course_id URL keyword argument
    def form_valid(self, form):
        form.instance.course_id = self.kwargs['course_id']
        return super().form_valid(form)

    def get_success_url(self):
        # Redirect back to the course detail view
        return reverse_lazy('courses:course_detail', kwargs={'pk': self.kwargs['course_id']})

class LessonCreateView(CreateView):
    model = Lesson
    form_class = LessonForm
    template_name = 'courses/lesson_form.html'
    # Assuming you have a module_id URL keyword argument
    def form_valid(self, form):
        form.instance.module_id = self.kwargs['module_id']
        return super().form_valid(form)

    def get_success_url(self):
        # Redirect back to the module detail page
        return reverse_lazy('courses:module_detail', kwargs={'pk': self.kwargs['module_id']})

