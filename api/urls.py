from django.urls import path
from . import views

urlpatterns = [
    path('get-games/', views.getGames),
    path('get-reviews/', views.getReviews),
    path('get-feed/', views.getFeed),

    path('add-review/', views.addReview),
]
