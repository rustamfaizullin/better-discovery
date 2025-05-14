from django.forms import ModelForm, ChoiceField
from django.forms.widgets import Select
from .models import Review

class ReviewForm(ModelForm):
    class Meta:
        model = Review
        fields = '__all__'
        exclude = ['game', 'author']