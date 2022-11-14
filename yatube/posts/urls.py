from django.urls import path

from . import views

app_name = 'posts'

urlpatterns = [
    path('profile/<str:username>/unfollow/',
         views.profile_unfollow,
         name='profile_unfollow'),
    path('profile/<str:username>/follow/',
         views.ProfileList.as_view(),
         name='profile_follow'),
    path('', views.YatubeHome.as_view(), name='index'),
    path('create/', views.PostCreate.as_view(), name='post_create'),
    path('group/<slug:slug>/', views.GroupView.as_view(), name='group_list'),
    path('profile/<str:username>/', views.profile, name='profile'),
    path('posts/<int:post_id>/edit/', views.post_edit, name='post_edit'),
    path('posts/<int:post_id>/', views.post_detail, name='post_detail'),
    path('posts/<int:post_id>/comment/',
         views.add_comment,
         name='add_comment'),
    path('follow/', views.follow_index, name='follow_index'),
]
