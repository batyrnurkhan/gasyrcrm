from django.db import models
from ckeditor.fields import RichTextField

class News(models.Model):
    title = models.CharField(max_length=255)
    photo = models.ImageField(upload_to='photos/%Y/%m/%d/')
    description = RichTextField()

    def __str__(self):
        return self.title
