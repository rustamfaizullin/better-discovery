from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('game/<str:pk>/', views.game, name='game'),
    path('feed/', views.feed, name='feed'),
    path('discover/', views.discover, name='discover'),

    path('login/', views.loginPage, name='login'),
    path('register/', views.registerPage, name='register'),
    path('logout/', views.logoutUser, name='logout'),

    path('user-profile/<str:pk>', views.userProfile, name='user-profile'),
    path('update-profile/', views.updateUser, name='update-profile'),

    path('delete/<str:pk>/', views.deleteReview, name='delete-review'),
    path('edit/<str:pk>/', views.editReview, name='edit-review'),
]
