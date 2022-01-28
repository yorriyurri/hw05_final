import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from posts.forms import PostForm
from posts.models import Comment, Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='hasnoname')
        cls.another_user = User.objects.create_user(username='noname')
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
        cls.post_1 = Post.objects.create(
            author=cls.user,
            text='Тестовый текст для поста_1',
            group=cls.group_1,
        )
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_form_post_create_post(self):
        """
        Проверяем, что при отправке валидной формы со страницы
        создания поста reverse('posts:create_post')
        создаётся новая запись в базе данных.
        """
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
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый текст для поста_2',
            'group': self.group_1.id,
            'image': uploaded
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(
            response,
            reverse('posts:profile', kwargs={'username': self.user.username})
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        created_post = Post.objects.order_by('id').last()
        self.assertEqual(created_post.text, form_data['text'])
        self.assertEqual(created_post.group.id, form_data['group'])
        self.assertIsNotNone(created_post.image, form_data['image'])

    def test_form_post_edit_post(self):
        """
        Проверяем, что при отправке валидной формы со страницы
        редактирования поста reverse('posts:post_edit', args=('post_id',))
        происходит изменение поста с post_id в базе данных.
        """
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый текст для поста_1.2',
            'group': self.group_2.id,
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post_1.id}),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(
            response,
            reverse('posts:post_detail', kwargs={'post_id': self.post_1.id})
        )
        self.assertEqual(Post.objects.count(), posts_count)
        edited_post = Post.objects.get(id=self.post_1.id)
        self.assertEqual(edited_post.text, form_data['text'])
        self.assertEqual(edited_post.group.id, form_data['group'])

    def test_form_post_create_post_by_anonim(self):
        """
        Создание поста под анонимом (кол-во постов БД не должно увеличиться).
        """
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Текст поста, созданного анонимом.',
            'group': self.group_1.id,
        }
        response = self.client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertRedirects(
            response,
            reverse('users:login') + '?next=' + reverse('posts:post_create')
        )

    def test_form_post_edit_post_by_anonim(self):
        """
        Редактирование под анонимом (пост не должен изменить значения полей).
        """
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Текст поста, отредактированного анонимом.',
            'group': self.group_2.id,
        }
        response = self.client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post_1.id}),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(
            response,
            reverse('posts:post_detail', kwargs={'post_id': self.post_1.id})
        )
        self.assertEqual(Post.objects.count(), posts_count)
        edited_post = Post.objects.get(id=self.post_1.id)
        self.assertNotEqual(edited_post.text, form_data['text'])
        self.assertNotEqual(edited_post.group.id, form_data['group'])

    def test_form_post_edit_post_by_noname(self):
        """
        Редактирование не автором (пост не должен изменить значения полей).
        """
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Текст поста, отредактированного не автором.',
            'group': self.group_2.id,
        }
        self.authorized_client.force_login(self.another_user)
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post_1.id}),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(
            response,
            reverse('posts:post_detail', kwargs={'post_id': self.post_1.id})
        )
        self.assertEqual(Post.objects.count(), posts_count)
        edited_post = Post.objects.get(id=self.post_1.id)
        self.assertNotEqual(edited_post.text, form_data['text'])
        self.assertNotEqual(edited_post.group.id, form_data['group'])

    def test_comment_form_by_anonim(self):
        """Аноним не может комментировать посты."""
        comments_count = Comment.objects.count()
        comment_form = {
            'post': self.post_1,
            'author': self.user,
            'text': 'Текст тестового комментария.',
        }
        self.client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': self.post_1.id}
            ),
            data=comment_form,
            follow=True,
        )
        self.assertEqual(Comment.objects.count(), comments_count)

    def test_comment_form_by_user(self):
        """Авторизованный пользователь может комментировать посты."""
        comments_count = Comment.objects.count()
        comment_form = {
            'post': self.post_1,
            'author': self.user,
            'text': 'Текст тестового комментария.',
        }
        self.authorized_client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': self.post_1.id}
            ),
            data=comment_form,
            follow=True,
        )
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        self.assertTrue(Comment.objects.filter(
            post=self.post_1,
            author=self.user,
            text='Текст тестового комментария.'
        ).exists())
