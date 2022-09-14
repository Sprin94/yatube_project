from django.shortcuts import render, get_object_or_404

from .models import Group, Post

COUNT_POSTS_ON_PAGE = 10


def index(request):
    posts = Post.objects.select_related('author')[:COUNT_POSTS_ON_PAGE]
    context = {
        'posts': posts,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):

    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()[:COUNT_POSTS_ON_PAGE]
    context = {
        'group': group,
        'posts': posts,
    }
    return render(request, 'posts/group_list.html', context)
