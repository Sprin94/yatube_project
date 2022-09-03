from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Post(models.Model):
    text = models.TextField()
    pub_date = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts'
    )
    group = models.ForeignKey('Group', blank=True, null=True, on_delete=models.CASCADE)

class Group(models.Model):
    title = models.CharField(max_length=50, verbose_name='Заголовок')
    slug = models.SlugField(max_length=100, unique=True, verbose_name='URL')
    description = models.TextField(verbose_name='Описание группы')

    def __str__(self) -> str:
        return self.title