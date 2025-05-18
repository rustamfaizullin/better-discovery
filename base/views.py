from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate
from django.db.models import Avg, Count
from django.db.models.functions import Coalesce
from django.contrib import messages
from django.http import HttpResponse
from .roblox_fetcher import RobloxFetcher
import datetime
from .forms import ReviewForm, UserForm, MyUserCreationForm
from .models import Game, Review, User
import asyncio
import time
from asgiref.sync import sync_to_async
from django.core.cache import cache

fetcher = RobloxFetcher()

def home(request):
    return redirect('feed')

def feed(request):
    games = list(Game.objects.annotate(
            average_rating=Coalesce(Avg('reviews__score'), 0.0), count=Count('reviews')
        ).order_by('-average_rating', '-count')[:49])
    feed_games = []

    for game in games:
        cached_game = cache.get(f'game_{game.id}')
        if cached_game:
            print(f'cache feed game - {game.id}')
            game.source_name = cached_game['source_name']
            game.icon_url = cached_game['icon_url']
        game.rating = game.average_rating
        print(f'feed game - {game.id}')
        feed_games.append(game)

    context = {'feed_games': feed_games}
    return render(request, 'base/feed.html', context)

def discover(request):
    search_query = request.GET.get('q') if request.GET.get('q') is not None else ''
    games_datas = fetcher.get_search_query(search_query)
    if search_query == '' or games_datas is None:
        return render(request, 'base/discover.html')
    return render(request, 'base/discover.html', {'games_datas': games_datas})

def game(request, pk):
    place_id = pk

    game_instance, _ = Game.objects.get_or_create(id=place_id)
    game_rate = game_instance.get_avg_rating()['avg_rating']

    cached_game = cache.get(f'game_{game_instance.id}')
    if cached_game:
        print('cache')
        get_cache_data(game_instance, cached_game)
    else:
        game_data, icon_url, thumbnail_urls = asyncio.run(fetcher.get_game_async(place_id))
        update_game_fields(game_instance, game_data, icon_url, thumbnail_urls, game_rate)
        setCache(place_id, game_data, icon_url, thumbnail_urls)

    reviews = Review.objects.filter(game=game_instance)

    form = ReviewForm()

    review_already_exists = None
    if request.user.is_authenticated:
        review_already_exists = Review.objects.filter(game=game_instance, author=request.user).exists()
    
    if request.method == "POST":
        form = ReviewForm(request.POST)
        if request.user.is_authenticated:
            if Review.objects.filter(game=game_instance, author=request.user):  # if user already have review he can't make another one
                return redirect('game', pk=place_id)
            if form.is_valid():
                Review.objects.create(
                    game=game_instance,
                    author=request.user,
                    body=request.POST.get('body'),
                    score=request.POST.get('score')
                )
                game_instance.rating = game_rate
                game_instance.save()
                messages.success(request, 'review succesfully applied')
            else:
                messages.error(request, 'review is not valid')
        return redirect('game', pk=place_id)

    context = {'thumbnail_urls': game_instance.thumbnails, 'game_data': game_instance, 'reviews': reviews, 'review_already_exists': review_already_exists, 'game_rate': game_rate,
               'form': form}
    return render(request, 'base/game.html', context)

def loginPage(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        try:
            user = User.objects.get(email=email)
        except:
            messages.error(request, 'user does not exist')

        user = authenticate(request, email=email, password=password)
        if user is not None:
            login(request, user)
            return redirect('feed')
        else:
            messages.error(request, 'username or password does not exist')

    context = {}
    return render(request, 'base/login.html', context)

def logoutUser(request):
    logout(request)
    return redirect('feed')

def registerPage(request):
    form = MyUserCreationForm()
    if request.method == "POST":
        form = MyUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = user.username.lower()
            user.save()
            login(request, user)
            return redirect('feed')
        else:
            messages.error(request, 'something went wrong')

    return render(request, 'base/register.html', {'form': form})

@login_required(login_url='login')
def deleteReview(request, pk):
    review = Review.objects.get(id=pk)
    place_id = review.game.id

    if request.user != review.author:
        return render(request, 'base/forbidden.html')
    if request.method == "POST":
        review.delete()
        messages.success(request, 'review succesfully deleted')
        return redirect('game', pk=place_id)
    return render(request, 'base/delete.html', {'review': review})

    
@login_required(login_url='login')
def editReview(request, pk):
    review = Review.objects.get(id=pk)
    form = ReviewForm(instance=review)
    place_id = review.game.id
    if request.user != review.author:
        return render(request, 'base/forbidden.html')
    if request.method == "POST":
        form = ReviewForm(request.POST)
        Review.objects.filter(id=pk).update(
            body=request.POST.get("body"),
            score=request.POST.get("score")
        )
        return redirect('game', pk=place_id)
    return render(request, 'base/edit.html', {'form': form})

def updateUser(request):
    user = request.user
    form = UserForm(instance=user)

    if request.method == "POST":
        form = UserForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            return redirect('user-profile', pk=user.id)
    
    return render(request, 'base/update-user.html', {'form': form})
        
def userProfile(request, pk):
    user = User.objects.get(id=pk)
    reviews = Review.objects.filter(author=user)
    context = {'user': user, 'reviews': reviews}

    return render(request , 'base/user-profile.html', context)

def setCache(place_id, game_data, icon_url, thumbnail_urls):
    cache.set(f'game_{place_id}', {
        'source_name': game_data.source_name,
        'source_description': game_data.source_description,
        'creator_id': game_data.creator_id,
        'creator_type': game_data.creator_type,
        'creator_name': game_data.creator_name,
        'visits': game_data.visits,
        'favorited_count': game_data.favorited_count,
        'created': game_data.created,
        'updated': game_data.updated,
        'avatar_type': game_data.avatar_type,
        'active': game_data.active,
        'icon_url': icon_url,
        'thumbnail_urls': thumbnail_urls
    }, timeout=100)

def update_game_fields(game_instance, game_data, icon_url, thumbnail_urls, rating):
    game_instance.source_name = game_data.source_name
    game_instance.source_description = game_data.source_description
    game_instance.creator_id = game_data.creator_id
    game_instance.creator_type = game_data.creator_type
    game_instance.creator_name = game_data.creator_name
    game_instance.visits = game_data.visits
    game_instance.favorited_count = game_data.favorited_count
    game_instance.created = game_data.created
    game_instance.updated = game_data.updated
    game_instance.avatar_type = game_data.avatar_type
    game_instance.active = game_data.active
    game_instance.icon_url = icon_url
    game_instance.thumbnails = thumbnail_urls
    game_instance.rating = rating
    game_instance.save()

def get_cache_data(game_instance, cached_game):
    game_instance.source_name = cached_game['source_name']
    game_instance.source_description = cached_game['source_description']
    game_instance.creator_id = cached_game['creator_id']
    game_instance.creator_type = cached_game['creator_type']
    game_instance.creator_name = cached_game['creator_name']
    game_instance.visits = cached_game['visits']
    game_instance.favorited_count = cached_game['favorited_count']
    game_instance.created = cached_game['created']
    game_instance.updated = cached_game['updated']
    game_instance.avatar_type = cached_game['avatar_type']
    game_instance.active = cached_game['active']
    game_instance.thumbnails = cached_game['thumbnail_urls']