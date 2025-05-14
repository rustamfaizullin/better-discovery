from rest_framework import serializers
from base.models import Game, Review

class GameSerializer(serializers.ModelSerializer):
  class Meta:
    model = Game
    fields = '__all__'

class ReviewSerializer(serializers.ModelSerializer):
  class Meta:
    model = Review
    fields = '__all__'