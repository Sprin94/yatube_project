from django.db import models


class Contact(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(
        help_text='Укажите действующий адрес электронной почты,'
    )
    subject = models.CharField(max_length=100)
    body = models.TextField()
    is_answered = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Контакт'
        verbose_name_plural = 'Контакты'
