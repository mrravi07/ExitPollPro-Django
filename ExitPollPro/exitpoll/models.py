from django.db import models
from django.utils import timezone

class State(models.Model):
    name = models.CharField(max_length=100)
    def __str__(self): return self.name

class ExitPoll(models.Model):
    state = models.ForeignKey(State, on_delete=models.CASCADE)
    party_name = models.CharField(max_length=100)
    votes = models.IntegerField()
    def __str__(self): return f"{self.state.name} - {self.party_name}"

class ConstituencyResult(models.Model):
    state = models.CharField(max_length=200)
    constituency = models.CharField(max_length=200)
    party = models.CharField(max_length=200)
    candidate = models.CharField(max_length=200)
    votes = models.IntegerField()
    winner_flag = models.BooleanField()
    def __str__(self): return f"{self.constituency} - {self.party}"

class MLResult(models.Model):
    model_name = models.CharField(max_length=200)
    accuracy = models.FloatField()
    confusion_matrix_image = models.ImageField(upload_to='charts/confusion_matrix/')
    trained_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return f"{self.model_name} - {self.accuracy}"

# New model for storing feedback
class Feedback(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    message = models.TextField()
    submitted_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f'Feedback from {self.name}'
