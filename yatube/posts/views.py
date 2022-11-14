from django.views.generic import ListView, CreateView
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin

from django.core.paginator import Paginator

from .forms import PostForm, CommentForm
from .models import Group, Post, User, Follow

COUNT_POSTS_ON_PAGE = 10


def get_page_obj(request, post_list):
    paginator = Paginator(post_list, COUNT_POSTS_ON_PAGE)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)


class YatubeHome(ListView):
    paginate_by = COUNT_POSTS_ON_PAGE
    template_name = 'posts/index.html'

    def get_queryset(self):
        return Post.objects.select_related('author').all()


class GroupView(ListView):
    paginate_by = COUNT_POSTS_ON_PAGE
    template_name = 'posts/group_list.html'

    def get_queryset(self):
        self.group = get_object_or_404(Group, slug=self.kwargs['slug'])
        return self.group.posts.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['group'] = self.group
        return context


class ProfileList(ListView):
    paginate_by = COUNT_POSTS_ON_PAGE
    template_name = 'posts/profile.html'

    def get_queryset(self):
        self.user = get_object_or_404(User, username=self.kwargs['username'])
        post_list = self.user.posts.all()
        self.amount_posts = post_list.count()
        return post_list

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            following = Follow.objects.filter(
                user=self.request.user,
                author=self.user).exists()
        else:
            following = True
        my_profile = self.user == self.request.user
        context['following'] = following
        context['author'] = self.user
        context['amount_posts'] = self.amount_posts
        context['my_profile'] = my_profile


def profile(request, username):
    user = get_object_or_404(User, username=username)
    post_list = user.posts.all()
    amount_posts = post_list.count()
    page_obj = get_page_obj(request, post_list)
    if request.user.is_authenticated:
        following = Follow.objects.filter(
            user=request.user,
            author=user).exists()
    else:
        following = True
    my_profile = user == request.user
    context = {
        'my_profile': my_profile,
        'following': following,
        'author': user,
        'amount_posts': amount_posts,
        'page_obj': page_obj,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = (Post.objects
            .select_related('author')
            .prefetch_related('comments')
            .get(id=post_id))
    amount_posts = post.author.posts.count()
    comments = post.comments.all()
    context = {
        'comments': comments,
        'form': CommentForm(),
        'post': post,
        'amount_posts': amount_posts
    }
    return render(request, 'posts/post_detail.html', context)


class PostCreate(LoginRequiredMixin, CreateView):
    template_name = 'posts/create_post.html'
    form_class = PostForm

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super(PostCreate, self).form_valid(form)

@login_required
def post_create(request):
    if request.method == 'POST':
        form = PostForm(
            request.POST,
            files=request.FILES or None,
        )
        if form.is_valid():
            new_post = form.save(commit=False)
            new_post.author = request.user
            new_post.save()
            return redirect('posts:profile', request.user.username)
        return render(request, 'posts/create_post.html', {'form': form})
    form = PostForm()
    return render(request, 'posts/create_post.html', {'form': form})


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.user != post.author:
        return redirect('posts:post_detail', post_id=post_id)
    if request.method == 'POST':
        form = PostForm(
            request.POST,
            instance=post,
            files=request.FILES or None,
        )
        if form.is_valid():
            form.save()
            return redirect('posts:post_detail', post_id=post_id)
    form = PostForm(instance=post)
    return render(request,
                  'posts/create_post.html',
                  {'form': form, 'is_edit': True, 'post': post}
                  )


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    follow = request.user.follower.values('author')
    post_list = Post.objects.filter(author_id__in=follow)
    page_obj = get_page_obj(request, post_list)
    context = {
        'page_obj': page_obj
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    if request.user.username != username:
        Follow.objects.get_or_create(
            user=request.user,
            author=User.objects.get(username=username)
        )
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    is_follow = Follow.objects.filter(
        user=request.user,
        author=User.objects.get(username=username)).exists()
    if is_follow:
        Follow.objects.get(
            user=request.user,
            author=User.objects.get(username=username)
        ).delete()
    return redirect('posts:profile', username=username)
