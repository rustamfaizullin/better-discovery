from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.http import HttpResponse
from .roblox_fetcher import RobloxFetcher
import datetime
from .models import Game, Review
import asyncio
import time

fetcher = RobloxFetcher()

def home(request):
    return redirect('feed')

def feed(request):
    feed_games, error_list, expected_games_ids = fetcher.get_feed()
    # feed_games, error_list, expected_games_ids = asyncio.run(fetcher.get_feed_async())
    MIN_RETURNED_THRESHOLD = 0.2

    if len(error_list) == 0:
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
    thumbnail_urls = fetcher.fetch_game_thumbnails(place_id)
    game_data = fetcher.fetch_game_data(place_id)

    game_instance, _ = Game.objects.get_or_create(id=place_id)
    reviews = Review.objects.filter(game=game_instance)

    number_reviews = len(reviews)
    if number_reviews > 0:
        sum_score = sum(review.score for review in reviews)
        game_rate = sum_score / number_reviews
    else:
        game_rate = 0

    check_review = None
    if request.user.is_authenticated:
        check_review = Review.objects.filter(game=game_instance, author=request.user).first() or 'no_review'
    
    if request.method == "POST":
        if request.user.is_authenticated:
            if Review.objects.filter(game=game_instance, author=request.user):  # if user already have review he can't make another one
                return redirect('game', pk=place_id)
            Review.objects.create(
                game=game_instance,
                author=request.user,
                body=request.POST.get('body'),
                score=request.POST.get('score')
            )
            return redirect('game', pk=place_id)
        return redirect('game', pk=place_id)

    context = {'thumbnail_urls': thumbnail_urls, 'game_data': game_data, 'reviews': reviews, 'check_review': check_review, 'game_rate': game_rate}
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
        return redirect('game', pk=place_id)
    return render(request, 'base/delete.html', {'review': review})

    
@login_required(login_url='login')
def editReview(request, pk):
    review = Review.objects.get(id=pk)
    place_id = review.game.id
    if request.user != review.author:
        return render(request, 'base/forbidden.html')
    if request.method == "POST":
        Review.objects.filter(id=pk).update(
            body=request.POST.get("body"),
            score=request.POST.get("score")
        )
        return redirect('game', pk=place_id)
    return render(request, 'base/edit.html', {'review': review})