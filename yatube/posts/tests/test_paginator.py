from django.conf import settings
from django.core.paginator import Paginator
from django.test import TestCase
from django.urls import reverse

from posts.models import Group, Post, User


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='hasnoname')
        cls.group_1 = Group.objects.create(
            title='Название группы_1 для теста',
            slug='test-slug_1',
            description='Тестовое описание группы_1'
        )
        cls.post = []
        for i in range(0, 15):
            cls.post.append(Post(
                author=cls.user,
                text='Текст для поста_' + str(i),
                group=cls.group_1
            ))
        cls.post = Post.objects.bulk_create(cls.post)
        p = Paginator(cls.post, settings.PER_PAGE_COUNT)
        cls.cnt = p.count

    def test_index_page_contains_10_records(self):
        '''На страницу index выводится по 10 постов'''
        response = self.client.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']),
                         settings.PER_PAGE_COUNT)

    def test_index_page_contains_5_records(self):
        '''На последнюю страницу index выводится остаток постов'''
        response = self.client.get(
            reverse('posts:index')
            + '?page=' + str(int(self.cnt / settings.PER_PAGE_COUNT) + 1)
        )
        self.assertEqual(len(response.context['page_obj']),
                         self.cnt % settings.PER_PAGE_COUNT)

    def test_group_list_page_contains_10_records(self):
        '''На страницу group_list выводится 10 постов'''
        response = self.client.get(reverse(
            'posts:group_list', kwargs={'slug': self.group_1.slug})
        )
        self.assertEqual(len(response.context['page_obj']),
                         settings.PER_PAGE_COUNT)

    def test_group_list_page_contains_5_records(self):
        '''На последнюю страницу group_list выводится остаток постов'''
        response = self.client.get(reverse(
            ('posts:group_list'), kwargs={'slug': self.group_1.slug})
            + '?page=' + str(int(self.cnt / settings.PER_PAGE_COUNT) + 1)
        )
        self.assertEqual(len(response.context['page_obj']),
                         self.cnt % settings.PER_PAGE_COUNT)

    def test_profile_page_contains_10_records(self):
        '''На страницу profile выводится 10 постов'''
        response = self.client.get(reverse(
            'posts:profile', kwargs={'username': self.user.username})
        )
        self.assertEqual(len(response.context['page_obj']),
                         settings.PER_PAGE_COUNT)

    def test_profile_page_contains_5_records(self):
        '''На последнюю страницу profile выводится остаток постов'''
        response = self.client.get(reverse(
            ('posts:profile'), kwargs={'username': self.user.username})
            + '?page=' + str(int(self.cnt / settings.PER_PAGE_COUNT) + 1)
        )
        self.assertEqual(len(response.context['page_obj']),
                         self.cnt % settings.PER_PAGE_COUNT)
