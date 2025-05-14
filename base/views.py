from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate
from django.db.models import Avg, Count
from django.db.models.functions import Coalesce
from django.contrib import messages
from django.http import HttpResponse
from .roblox_fetcher import RobloxFetcher
import datetime
from .forms import ReviewForm
from .models import Game, Review
import asyncio
import time

fetcher = RobloxFetcher()

def home(request):
    return redirect('feed')

def feed(request):
    games_ids_ratings = tuple(Game.objects.annotate(
            average_rating=Coalesce(Avg('reviews__score'), 0.0), count=Count('reviews')
        ).order_by('-average_rating', '-count')[:49].values_list('id', 'average_rating', flat=False))
    feed_games, error_list, expected_games_ids = asyncio.run(fetcher.get_feed_async(games_ids_ratings))
    MIN_RETURNED_THRESHOLD = 0.2

    if not error_list:
        context = {'feed_games': feed_games}
        return render(request, 'base/feed.html', context)
    elif len(error_list) < len(expected_games_ids) * MIN_RETURNED_THRESHOLD:
        for game_id in error_list:
            try:
                game = Game.objects.get(id=game_id)
                Review.objects.filter(game=game).delete()
                game.delete()
            except Game.DoesNotExist:
                continue
        return redirect('feed')

def discover(request):
    search_query = request.GET.get('q') if request.GET.get('q') is not None else ''
    games_datas = fetcher.get_search_query(search_query)
    if search_query == '' or games_datas is None:
        return render(request, 'base/discover.html')
    return render(request, 'base/discover.html', {'games_datas': games_datas})

def game(request, pk):
    place_id = pk

    thumbnail_urls, game_data = asyncio.run(fetcher.get_game_async(place_id))

    game_instance, created = Game.objects.get_or_create(id=place_id)

    if created or game_instance.outdated:
        thumbnail_urls, game_data = asyncio.run(fetcher.get_game_async(place_id))
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
        # game_instance.icon_url = game_data.icon_url
        game_instance.thumbnails = list(thumbnail_urls)
        game_instance.save()
        
    reviews = Review.objects.filter(game=game_instance)

    game_rate = game_instance.get_avg_rating()['avg_rating']

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
                messages.success(request, 'review succesfully applied')
            else:
                messages.error(request, 'review is not valid')
        return redirect('game', pk=place_id)

    context = {'thumbnail_urls': game_instance.thumbnails, 'game_data': game_instance, 'reviews': reviews, 'review_already_exists': review_already_exists, 'game_rate': game_rate,
               'form': form}
    return render(request, 'base/game.html', context)

def loginPage(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        try:
            user = User.objects.get(username=username)
        except:
            messages.error(request, 'user does not exist')

        user = authenticate(request, username=username, password=password)
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
    form = UserCreationForm()
    if request.method == "POST":
        form = UserCreationForm(request.POST)
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