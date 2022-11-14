from django.shortcuts import render
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse_lazy, reverse
from django.views.generic import CreateView, FormView, View
from django.contrib.auth.views import LoginView, PasswordResetConfirmView
from django.contrib.auth.forms import UserCreationForm
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.http import HttpResponseRedirect, HttpResponse
from django.utils.encoding import force_bytes
from django.core.mail import EmailMessage
from django.core.exceptions import ValidationError

from .forms import ContactForm, SignupForm, UserPasswordResetForm
from posts.models import User
from users.tasks import check_activation_new_user
from .token import TokenGenerator


class ViewSignupUser(FormView):
    form_class = SignupForm
    success_url = reverse_lazy('posts:index')
    template_name = 'users/signup.html'

    def form_valid(self, form):
        user = form.save(commit=False)
        user.is_active = False
        user.save()
        check_activation_new_user.apply_async(args=[user.pk], countdown=360)
        current_site = get_current_site(self.request)
        mail_subject = 'Activation link has been sent to your email id'
        message = render_to_string('users/acc_active_email.html', {
            'user': user,
            'domain': current_site.domain,
            'uid': urlsafe_base64_encode(force_bytes(user.pk)),
            'token': TokenGenerator().make_token(user),
        })
        to_email = form.cleaned_data.get('email')
        email = EmailMessage(
            mail_subject, message, to=[to_email]
        )
        email.send()
        return HttpResponse(
            'Please confirm your email address to complete the registration')


class ViewUserSingupActivate(View):

    def dispatch(self, *args, **kwargs):
        user = self.get_user(kwargs['uidb64'])
        if user is not None and TokenGenerator().check_token(user, kwargs['token']):
            user.is_active = True
            user.save()
            return HttpResponseRedirect(reverse('users:login'))
        else:
            return HttpResponse('Activation link is invalid!')

    def get_user(self, uidb64):
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = User._default_manager.get(pk=uid)
        except (
                TypeError,
                ValueError,
                OverflowError,
                User.DoesNotExist,
                ValidationError,
        ):
            user = None
        return user




def user_contact(request):
    form = ContactForm()
    return render(request, 'users/contact.html', {'form': form})
