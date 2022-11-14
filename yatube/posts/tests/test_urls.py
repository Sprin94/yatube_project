from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse

from ..models import Post, Group

User = get_user_model()


class StaticURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_homepage(self):
        response = self.guest_client.get(reverse('posts:index'))
        self.assertEqual(response.status_code, HTTPStatus.OK)


class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.user = User.objects.create_user(username='NoName')
        cls.user_second = User.objects.create_user(username='Noname2')
        Group.objects.create(
            title='test',
            slug='test',
            description='test group'
        )
        Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
            group=Group.objects.get(title='test')
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client_second = Client()
        self.authorized_client_second.force_login(self.user_second)

    def test_urls_uses_correct_template(self):
        templates_url_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:profile',
                    kwargs={'username': 'NoName'}): 'posts/profile.html',
            reverse('posts:post_edit',
                    kwargs={'post_id': 1}): 'posts/create_post.html',
            reverse('posts:post_detail',
                    kwargs={'post_id': 1}): 'posts/post_detail.html',
            reverse('posts:group_list',
                    kwargs={'slug': 'test'}): 'posts/group_list.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_404(self):
        url = '/post/'
        response = self.guest_client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_create_url_redirect(self):
        response = self.guest_client.get(reverse('posts:post_create'))
        self.assertRedirects(
            response,
            reverse('users:login') + '?next=/create/'
        )

    def test_edit_url_redirect(self):
        url = reverse('posts:post_edit', kwargs={'post_id': 1})
        response = self.authorized_client_second.get(url)
        self.assertRedirects(
            response,
            reverse('posts:post_detail', kwargs={'post_id': 1}))
