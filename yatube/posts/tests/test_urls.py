from http import HTTPStatus

from django.core.cache import cache
from django.test import Client, TestCase

from posts.models import Group, Post, User


class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Название группы для теста',
            slug='test-slug',
            description='Тестовое описание группы'
        )

    def setUp(self):
        self.user = User.objects.create_user(username='hasnoname')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.post = Post.objects.create(
            text='Тестовый текст',
            author=self.user
        )

    def test_pages_at_desired_location(self):
        """
        Страницы index, group_list, profile, post_detail
        доступны любому пользователю.
        """
        page_urls = [
            '/',
            '/group/{slug}/'.format(slug=self.group.slug),
            '/profile/{username}/'.format(username=self.user),
            '/posts/{post_id}/'.format(post_id=self.post.id),
        ]
        for url in page_urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_unexisting_page_url_exists_at_desired_location(self):
        """Страница не существует."""
        response = self.client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertTemplateUsed(response, 'core/404.html')

    def test_create_page_url_exists_at_desired_location(self):
        """Страница create доступна авторизованному пользователю."""
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_edit_page_url_exists_at_desired_location(self):
        """Страница post_edit доступна автору поста."""
        response = self.authorized_client.get(
            '/posts/{post_id}/edit/'.format(post_id=self.post.id)
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        cache.clear()
        templates_url_names = {
            '/': 'posts/index.html',
            '/group/{slug}/'.format(slug=self.group.slug):
                'posts/group_list.html',
            '/profile/{username}/'.format(username=self.user):
                'posts/profile.html',
            '/posts/{post_id}/'.format(post_id=self.post.id):
                'posts/post_detail.html',
            '/create/': 'posts/create_post.html',
            '/posts/{post_id}/edit/'.format(post_id=self.post.id):
                'posts/create_post.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template, 'Шаблон не найден')
