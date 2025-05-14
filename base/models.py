from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db.models import Avg

class Game(models.Model):
  id = models.CharField(max_length=200, primary_key=True)
  source_name = models.TextField(blank=True, null=True)
  source_description = models.TextField(blank=True, null=True)
  creator_id = models.TextField(blank=True, null=True)
  creator_type = models.TextField(blank=True, null=True)
  creator_name = models.TextField(blank=True, null=True)
  visits = models.TextField(blank=True, null=True)
  favorited_count = models.TextField(blank=True, null=True)
  created = models.TextField(blank=True, null=True)
  updated = models.TextField(blank=True, null=True)
  avatar_type = models.TextField(blank=True, null=True)
  active = models.TextField(blank=True, null=True)
  icon_url = models.TextField(blank=True, null=True)
  outdated = models.BooleanField(default=True)
  thumbnails = models.JSONField(default=list, blank=True, null=True)

  def __str__(self):
    return str(self.id)
  
  def get_avg_rating(self):
    return Game.objects.filter(id=self.id).aggregate(avg_rating=Avg('reviews__score'))

class Review(models.Model):
  game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='reviews')
  author = models.ForeignKey(User, on_delete=models.CASCADE)
  body = models.TextField()
  created = models.DateTimeField(auto_now_add=True)
  score = models.IntegerField(
    choices=[(i, str(i)) for i in range(11)],
    default=0,
    validators=[MaxValueValidator(10), MinValueValidator(0)]
  )

  def __str__(self):
    return str(self.body)