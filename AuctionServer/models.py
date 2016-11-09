from __future__ import unicode_literals
from datetime import datetime, timedelta

from django.db import models
from django.contrib.auth.models import User

# Create your models here.


class Auction(models.Model):
    name = models.CharField(max_length=50)
    seller = models.ForeignKey(User,on_delete=models.CASCADE)
    description = models.TextField()
    priceMin = models.FloatField()
    time = models.DateTimeField()
    due = models.DateTimeField()
    a_hash = models.TextField()


class Bid(models.Model):
    auction = models.ForeignKey(Auction, on_delete=models.CASCADE)
    bidder = models.ForeignKey(User, on_delete=models.CASCADE)
    price = models.FloatField()
    time = models.DateTimeField()