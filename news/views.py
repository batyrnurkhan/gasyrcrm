from django.shortcuts import render, get_object_or_404
from .models import News

# Create your views here.
def news_list(request):
    news_articles = News.objects.all().order_by('-created_at')
    context = {
        'news_articles': news_articles
    }
    return render(request, 'news/news_list.html', context)

def news_detail(request, news_id):
    news = get_object_or_404(News, id=news_id)
    other_articles = News.objects.exclude(id=news_id)[:5]
    return render(request, 'news/news_detail.html', {'news': news, 'other_articles': other_articles})