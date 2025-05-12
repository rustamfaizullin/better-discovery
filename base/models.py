from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator

class Game(models.Model):
  id = models.CharField(max_length=200, primary_key=True)

  def __str__(self):
    return str(self.id)

class Review(models.Model):
  game = models.ForeignKey(Game, on_delete=models.CASCADE)
  author = models.ForeignKey(User, on_delete=models.CASCADE)
  body = models.TextField()
  created = models.DateTimeField(auto_now_add=True)
  score = models.IntegerField(default=0, validators=[MaxValueValidator(10), MinValueValidator(0)])

  def __str__(self):
    return str(self.body)