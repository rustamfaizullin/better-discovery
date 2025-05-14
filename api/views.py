from rest_framework.response import Response
from rest_framework.decorators import api_view
from base.models import Game, Review
from .serializers import GameSerializer, ReviewSerializer
from django.db.models import Avg, Count
from django.db.models.functions import Coalesce

@api_view(['GET'])
def getFeed(request):
    games_ids_ratings = Game.objects.annotate(
                average_rating=Coalesce(Avg('reviews__score'), 0.0), count=Count('reviews')
            ).order_by('-average_rating', '-count')[:49]
    serializer = GameSerializer(games_ids_ratings, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def getGames(request):
    games_ids_ratings = Game.objects.annotate(
                average_rating=Coalesce(Avg('reviews__score'), 0.0), count=Count('reviews')
            ).order_by('-average_rating', '-count')
    serializer = GameSerializer(games_ids_ratings, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def getReviews(request):
    reviews = Review.objects.all()
    serializer = ReviewSerializer(reviews, many=True)
    return Response(serializer.data)

@api_view(['POST'])
def addReview(request):
    serializer = ReviewSerializer(data=request.data)
    if serializer.is_valid():
        serializer
    return Response(serializer.data)