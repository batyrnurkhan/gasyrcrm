from django.contrib import admin
from .models import News

class NewsAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'created_at')
    search_fields = ('title', 'content')
    list_filter = ('created_at', 'author')
    fields = ('title', 'content', 'quote', 'advertisement', 'image', 'author')

admin.site.register(News, NewsAdmin)
