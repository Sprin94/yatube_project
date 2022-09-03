# posts/urls.py
from django.urls import path

from . import views

app_name = 'posts'

urlpatterns = [
    #главная страница
    path('', views.index, name='index'),
    #посты группы
    path('groups/<slug:slug>/', views.group_posts, name='group_posts'),
]