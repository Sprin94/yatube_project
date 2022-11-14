from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordResetForm, UserCreationForm
from django.core.exceptions import ValidationError

from .models import Contact
from .tasks import send_email_password_reset

User = get_user_model()


class SignupForm(UserCreationForm):
    email = forms.EmailField(
        widget=forms.TextInput(
            attrs={
                'class': 'input',
                'type': 'email',
                'placeholder': "Email"
                }),
        max_length=200
    )

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
             raise ValidationError('Пользователь с таким адресом уже существует.')
        return email

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

class UserPasswordResetForm(PasswordResetForm):

    def send_mail(self, subject_template_name, email_template_name, context,
                  from_email, to_email, html_email_template_name=None):
        context['user'] = context['user'].id

        send_email_password_reset.delay(
            subject_template_name=subject_template_name,
            email_template_name=email_template_name,
            context=context, from_email=from_email, to_email=to_email,
            html_email_template_name=html_email_template_name)


class ContactForm(forms.ModelForm):
    class Meta:
        model = Contact
        fields = ('name', 'email', 'subject', 'body')

