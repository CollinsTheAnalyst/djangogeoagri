from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from .models import BlogPost


def blog_list(request):
    query = request.GET.get('q', '')
    if query:
        blog_posts = BlogPost.objects.filter(title__icontains=query)
    else:
        blog_posts = BlogPost.objects.all().order_by('-created_at')

    recent_posts = BlogPost.objects.order_by('-created_at')[:5]

    context = {
        'blog_posts': blog_posts,
        'recent_posts': recent_posts,
    }
    return render(request, 'blog/list.html', context)


def blog_detail(request, slug):
    post = get_object_or_404(BlogPost, slug=slug)
    return render(request, "blog/detail.html", {"post": post})

