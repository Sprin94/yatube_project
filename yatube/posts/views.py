from django.http import HttpResponse

from django.shortcuts import render


def index(request):
    template = 'posts/index.html'
    context = {}
    context['text'] = 'Это главная страница'
    return render(request, template, context)

def group_posts(request, slug):
    template = 'posts/group_list.html'
    context = {}
    context['text'] = 'Здесь будет информация о группах проекта Yatube'
    return render(request, template, context)