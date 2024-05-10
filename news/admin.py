from django.contrib import admin
from .models import News
from ckeditor.widgets import CKEditorWidget
from django import forms

class NewsAdminForm(forms.ModelForm):
    class Meta:
        model = News
        fields = '__all__'
        widgets = {
            'description': CKEditorWidget(),
        }

class NewsAdmin(admin.ModelAdmin):
    form = NewsAdminForm

admin.site.register(News, NewsAdmin)
