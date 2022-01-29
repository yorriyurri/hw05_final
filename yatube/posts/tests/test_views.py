import shutil
import tempfile

from django import forms
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Follow, Comment, Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


class PostsViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='hasnoname')
        cls.user_2 = User.objects.create_user(username='idol')
        cls.group_1 = Group.objects.create(
            title='Название группы_1 для теста',
            slug='test-slug_1',
            description='Тестовое описание группы_1'
        )
        cls.group_2 = Group.objects.create(
            title='Название группы_2 для теста',
            slug='test-slug_2',
            description='Тестовое описание группы_2'
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.post_1 = Post.objects.create(
            author=cls.user,
            text='Тестовый текст для поста_1',
            group=cls.group_1,
            image=cls.uploaded,
        )
        cls.comment = Comment.objects.create(
            post=cls.post_1,
            author=cls.user,
            text='Текст первого тестового комментария.'
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        cache.clear()
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', kwargs={'slug': self.group_1.slug}):
                'posts/group_list.html',
            reverse('posts:profile', kwargs={'username': self.user.username}):
                'posts/profile.html',
            reverse('posts:post_detail', kwargs={'post_id': self.post_1.id}):
                'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:post_edit', kwargs={'post_id': self.post_1.id}):
                'posts/create_post.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_pages_show_correct_context(self):
        """Шаблон страницы сформирован с правильным контекстом."""
        cache.clear()
        context_url = (
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group_1.slug}),
            reverse('posts:profile', kwargs={'username': self.user.username}),
        )
        for url in context_url:
            with self.subTest():
                response = self.client.get(url)
                first_object = response.context['page_obj'][0]
                self.assertEqual(
                    first_object.text,
                    self.post_1.text)
                self.assertEqual(
                    first_object.id, self.post_1.id
                )
                self.assertEqual(
                    first_object.group.title,
                    self.group_1.title
                )
                self.assertEqual(
                    first_object.author.username, self.user.username
                )
                self.assertEqual(
                    first_object.image, self.post_1.image
                )

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post_1.id})
        )
        self.assertEqual(
            response.context['post'].text, self.post_1.text
        )
        self.assertEqual(
            response.context['post'].image, self.post_1.image
        )
        comment = response.context['comments'][0]
        self.assertEqual(comment, self.comment)

    def test_post_create_page_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_page_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post_1.id}))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_appears_on_pages(self):
        """
        Созданный пост появляется на страницах:
        index, group_list, profile.
        """
        cache.clear()
        urls = (
            reverse('posts:index'),
            reverse('posts:profile', kwargs={'username': self.user.username}),
            reverse('posts:group_list',
                    kwargs={'slug': self.group_1.slug}),
        )
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                first_object = response.context['page_obj'][0]
                self.assertEqual(first_object.author, self.user)
                self.assertEqual(first_object.text,
                                 self.post_1.text
                                 )
                self.assertEqual(first_object.group.title,
                                 self.group_1.title
                                 )

    def test_cache_on_index_page(self):
        """Тестирование кэша на главной странице."""
        first_response = self.client.get(reverse('posts:index'))
        content_1 = first_response.content
        Post.objects.all().delete()
        second_response = self.client.get(reverse('posts:index'))
        content_2 = second_response.content
        self.assertEqual(content_1, content_2)
        cache.clear()
        third_response = self.client.get(reverse('posts:index'))
        content_3 = third_response.content
        self.assertNotEqual(content_1, content_3)

    def test_authorized_client_can_follow(self):
        """Авторизованный пользователь может подписываться на других пользователей."""
        self.authorized_client.get(reverse(
            'posts:profile_follow',
            kwargs={'username': self.user_2.username}
        ))
        subscribe = Follow.objects.get(user=self.user)
        self.assertEqual(self.user_2, subscribe.author)

    def test_authorized_client_can_unfollow(self):
        """
        Авторизованный пользователь может удалять из подписок других пользователей.
        """
        self.authorized_client.get(reverse(
            'posts:profile_follow',
            kwargs={'username': self.user_2.username}
        ))
        Follow.objects.get(user=self.user)
        one_follower = Follow.objects.count()
        self.authorized_client.get(reverse(
            'posts:profile_unfollow',
            kwargs={'username': self.user_2.username}
        ))
        no_followers = Follow.objects.count()
        self.assertEqual(one_follower - 1, no_followers)

    def test_followers_get_post(self):
        """
        Новая запись пользователя появляется в ленте тех,
        кто на него подписан и не появляется в ленте тех, кто не подписан.
        """
        self.authorized_client.get(reverse(
            'posts:profile_follow',
            kwargs={'username': self.user_2.username}
        ))
        idols_post = Post.objects.create(
            text='Тестовый пост кумира',
            group=self.group_1,
            author=self.user_2,
        )
        user_3 = User.objects.create_user(username='dont_like_idol')
        authorized_user_3 = Client()
        authorized_user_3.force_login(user_3)
        user_response = self.authorized_client.get(reverse(
            'posts:follow_index'))
        user_3_response = authorized_user_3.get(reverse(
            'posts:follow_index'))
        self.assertEqual(user_response.context['page_obj'][0], idols_post)
        self.assertNotIn(idols_post, user_3_response.context['page_obj'])
