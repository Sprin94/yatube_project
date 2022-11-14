import django.contrib.auth.views as djv
from django.urls import path

from . import views

app_name = 'users'

urlpatterns = [
    path(
        'logout/',
        djv.LogoutView.as_view(template_name='users/logged_out.html'),
        name='logout'
    ),
    path(
        'signup/',
        views.ViewSignupUser.as_view(),
        name='signup'
    ),
    path(
        'login/',
        djv.LoginView.as_view(template_name='users/login.html'),
        name='login'
    ),
    path(
        'password_change/',
        djv.PasswordChangeView.as_view(
            template_name='users/password_change_form.html'
        ),
        name='password_change'
    ),
    path(
        'password-change/done/',
        djv.PasswordChangeDoneView.as_view(
            template_name='users/password_change_done.html'
        ),
        name='password_change_done'
    ),
    path(
        'password-reset/',
        djv.PasswordResetView.as_view(
            template_name='users/password_reset_form.html'
        ),
        name='password_reset'
    ),
    path(
        'password_reset/done/',
        djv.PasswordResetDoneView.as_view(
            template_name='users/password_reset_done.html'
        ),
        name='password_reset_done'
    ),
    path(
        'reset/<uidb64>/<token>/',
        djv.PasswordResetConfirmView.as_view(
            template_name='users/password_reset_confirm.html'
        ),
        name='password_reset_confrim'
    ),
    path(
        'reset/done/',
        djv.PasswordResetCompleteView.as_view(
            template_name='users/password_reset_complete.html'
        ),
        name='password_reset_complete'
    ),
    path(
        'user/singup/<uidb64>/<token>/',
        views.ViewUserSingupActivate.as_view(),
        name='active_user')
]
