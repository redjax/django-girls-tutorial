from django.contrib import admin

## Import the Post model in the blog app
from .models import Post

## Make the Post object available in the blog admin site
admin.site.register(Post)
