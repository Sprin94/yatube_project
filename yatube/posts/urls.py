# posts/urls.py
from django.urls import path


from . import views


urlpatterns = [
    #главная страница
    path('', views.index),
    #посты группы
    path('groups/<slug:slug>/', views.group_posts),
]