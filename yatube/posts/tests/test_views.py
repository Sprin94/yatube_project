import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django import forms
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache

from ..models import Group, Post, Follow
from ..views import COUNT_POSTS_ON_PAGE

User = get_user_model()
COUNT_TEMP_POST = 13
SECOND_PAGE_POST = 3
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class ViewsTests(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.user = User.objects.create_user(username='NoName')
        cls.user_second = User.objects.create_user(username='NoName2')
        cls.user_third = User.objects.create_user(username='NoName3')
        Follow.objects.create(user=cls.user_third, author=cls.user)
        cls.group = Group.objects.create(
            title='test',
            slug='test',
            description='test group'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
            group=cls.group,
            image=uploaded
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client_third = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client_second = Client()
        self.authorized_client_second.force_login(self.user_second)
        self.authorized_client_third.force_login(self.user_third)

    def test_pages_uses_correct_template(self):
        template_pagaes_name = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:group_list',
                    kwargs={'slug': 'test'}): 'posts/group_list.html',
            reverse('posts:profile',
                    kwargs={'username': 'NoName'}): 'posts/profile.html',
            reverse('posts:post_edit',
                    kwargs={'post_id': 1}): 'posts/create_post.html',
            reverse('posts:post_detail',
                    kwargs={'post_id': 1}): 'posts/post_detail.html',
            'post': 'core/404.html'
        }
        for reverse_name, template in template_pagaes_name.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        response = self.authorized_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        self.assertEqual(first_object.text, 'Тестовый текст')
        self.assertEqual(first_object.group.title, 'test')
        self.assertEqual(first_object.author.username, 'NoName')
        self.assertEqual(first_object.image, self.post.image)

    def test_group_list_show_correct_context(self):
        response = self.authorized_client.get(reverse('posts:group_list',
                                                      kwargs={'slug': 'test'}))
        for post in response.context['page_obj']:
            self.assertEqual(post.group, Group.objects.get(slug='test'))
            if getattr(post, 'image') is not None:
                self.assertEqual(post.image, self.post.image)

    def test_profile_list_show_correct_context(self):
        response = self.authorized_client.get(reverse(
            'posts:profile',
            kwargs={'username': 'NoName'}
        ))
        for post in response.context['page_obj']:
            self.assertEqual(post.author.username, 'NoName')
            if getattr(post, 'image') is not None:
                self.assertEqual(post.image, self.post.image)

    def test_detail_post_show_correct_context(self):
        response = self.authorized_client.get(reverse(
            'posts:post_detail',
            kwargs={'post_id': 1}
        ))
        self.assertEqual(response.context['post'].text, 'Тестовый текст')
        self.assertEqual(response.context['post'].image, self.post.image)

    def _assert_post(self, response):
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_edit_post_show_correct_context(self):
        response = self.authorized_client.get(reverse(
            'posts:post_edit',
            kwargs={'post_id': 1}
        ))
        self._assert_post(response)

    def test_create_post_show_correct_context(self):
        response = self.authorized_client.get(reverse('posts:post_create'))
        self._assert_post(response)

    def test_edit_post_another_user(self):
        response = self.authorized_client_second.get(reverse(
            'posts:post_edit',
            kwargs={'post_id': 1}
        ))
        self.assertRedirects(
            response,
            reverse('posts:post_detail', kwargs={'post_id': 1})
        )

    def test_only_auth_user_make_comment(self):
        response = self.guest_client.get(reverse(
            'posts:add_comment',
            kwargs={'post_id': 1}
        ))
        self.assertRedirects(response,
                             reverse('users:login')
                             + '?next=%2Fposts%2F1%2Fcomment%2F')

    def test_add_comments_on_page(self):
        response = self.authorized_client_second.get(reverse(
            'posts:post_detail',
            kwargs={'post_id': 1}
        ))
        count_comments = response.context['comments'].count()
        self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': 1}),
            data={'text': 'Тестовый текст комментария'},
            follow=True
        )
        response = self.authorized_client_second.get(reverse(
            'posts:post_detail',
            kwargs={'post_id': 1}
        ))
        self.assertEqual(response.context['comments'].count(),
                         count_comments + 1)

    def test_cache_index_page(self):
        response = self.guest_client.get(reverse('posts:index'))
        index_content = response.content
        form_data = {
            'text': 'Тестовый текст',
            'group': self.group.id,
        }
        self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        response = self.guest_client.get(reverse('posts:index'))
        index_content_cache = response.content
        self.assertEqual(index_content_cache, index_content)
        cache.clear()
        response = self.guest_client.get(reverse('posts:index'))
        self.assertNotEqual(response.content, index_content_cache)

    def test_follow(self):
        self.authorized_client.get(
            reverse('posts:profile_follow', kwargs={'username': 'NoName2'}))
        self.assertTrue(Follow.objects.get(
            user=self.user.id,
            author=self.user_second.id))

    def test_unfollow(self):
        Follow.objects.create(
            user=self.user,
            author=self.user_second)
        self.authorized_client.get(
            reverse('posts:profile_unfollow', kwargs={'username': 'NoName2'}))
        self.assertTrue(not Follow.objects.filter(
            user=self.user.id,
            author=self.user_second.id).exists())

    def _get_count_posts_follow(self, client):
        response = client.get(
            reverse('posts:follow_index')
        )
        return len(response.context['page_obj'])

    def test_new_post_visible_follower(self):
        count_before = self._get_count_posts_follow(
            self.authorized_client_third)
        Post.objects.create(
            author=self.user,
            text='Тестовый текст 100500',
            group=self.group,
        )
        count_after = self._get_count_posts_follow(
            self.authorized_client_third)
        self.assertEqual(count_before + 1, count_after)

    def test_new_post_invisible_not_follower(self):
        count_before = self._get_count_posts_follow(
            self.authorized_client_second)
        Post.objects.create(
            author=self.user,
            text='Тестовый текст 100500',
            group=self.group,
        )
        count_after = self._get_count_posts_follow(
            self.authorized_client_second)
        self.assertEqual(count_before, count_after)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.user = User.objects.create(username='NoName')
        cls.group = Group.objects.create(
            title='test',
            slug='test',
            description='test group'
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        for post_temp in range(COUNT_TEMP_POST):
            Post.objects.create(
                text=f'text{post_temp}',
                author=self.user,
                group=self.group
            )

    def _first_page_contains_ten_records(self, reverse_name):
        response = self.authorized_client.get(reverse_name)
        self.assertEqual(
            len(response.context['page_obj']),
            COUNT_POSTS_ON_PAGE)

    def _second_page_contains_three_records(self, reverse_name):
        response = self.authorized_client.get(
            reverse_name + '?page=2')
        self.assertEqual(
            len(response.context['page_obj']),
            SECOND_PAGE_POST)

    def test_paginator(self):
        templates_pages_names = {
            'posts/index.html': reverse('posts:index'),
            'posts/group_list.html': reverse(
                'posts:group_list',
                kwargs={'slug': self.group.slug}),
            'posts/profile.html': reverse(
                'posts:profile',
                kwargs={'username': self.user}),
        }
        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                self._first_page_contains_ten_records(reverse_name)
                self._second_page_contains_three_records(reverse_name)


class SecondCreatePostTest(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.user = User.objects.create_user(username='NoName')
        cls.group = Group.objects.create(
            title='test',
            slug='test',
            description='test group'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
            group=cls.group
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_post_per_page(self):
        templates_pages_names = {
            'posts/index.html': reverse('posts:index'),
            'posts/group_list.html': reverse(
                'posts:group_list',
                kwargs={'slug': self.group.slug}),
            'posts/profile.html': reverse(
                'posts:profile',
                kwargs={'username': self.user}),
        }
        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                first_post = response.context['page_obj'][0]
                self.assertEqual(first_post, self.post)
