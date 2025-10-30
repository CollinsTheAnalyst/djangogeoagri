from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from .models import BlogPost, Category


def blog_list(request, category_slug=None):
    # Fetch all categories
    categories = Category.objects.all().order_by('name')

    # Handle search
    query = request.GET.get('q', '')

    # Base queryset
    blog_posts = BlogPost.objects.all().order_by('-created_at')

    # Apply search filter if query exists
    if query:
        blog_posts = blog_posts.filter(
            Q(title__icontains=query) | Q(content__icontains=query)
        )

    # Filter by category if provided
    active_category = None
    if category_slug:
        active_category = get_object_or_404(Category, slug=category_slug)
        blog_posts = blog_posts.filter(category=active_category)

    # Fetch recent posts (for sidebar)
    recent_posts = BlogPost.objects.order_by('-created_at')[:5]

    context = {
        'blog_posts': blog_posts,
        'recent_posts': recent_posts,
        'categories': categories,
        'active_category': active_category,
        'query': query,
    }
    return render(request, 'blog/list.html', context)


def blog_detail(request, slug):
    post = get_object_or_404(BlogPost, slug=slug)

    # Get other posts to show as snippets (excluding current one)
    related_posts = BlogPost.objects.exclude(id=post.id).order_by('-created_at')[:3]

    context = {
        "post": post,
        "related_posts": related_posts,
    }
    return render(request, "blog/detail.html", context)

