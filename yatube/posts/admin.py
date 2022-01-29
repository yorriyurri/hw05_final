from django.contrib import admin

from .models import Comment, Follow, Group, Post


class GroupAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'description',)
    search_fields = ('title',)
    prepopulated_fields = {"slug": ("title",)}
    empty_value_display = '-пусто-'


admin.site.register(Group, GroupAdmin)


class PostAdmin(admin.ModelAdmin):
    list_display = ('pk', 'text', 'pub_date', 'author', 'group',)
    list_editable = ('group',)
    search_fields = ('text',)
    list_filter = ('pub_date',)
    empty_value_display = '-пусто-'


admin.site.register(Post, PostAdmin)


class CommentAdmin(admin.ModelAdmin):
    list_display = ('text', 'author', 'created', 'post',)
    search_fields = ('text', 'author',)
    list_filter = ('created', 'author',)


admin.site.register(Comment, CommentAdmin)


class FollowAdmin(admin.ModelAdmin):
    list_display = ('user', 'author',)
    search_fields = ('user', 'author',)


admin.site.register(Follow, FollowAdmin)
