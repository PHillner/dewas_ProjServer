from __future__ import unicode_literals
from datetime import datetime, timedelta

from django.db import models

# Create your models here.


class Auction(models.Model):
    name = models.CharField(max_length=50)
    seller = models.CharField(max_length=30)
    description = models.TextField()
    priceMin = models.FloatField()
    time = models.DateTimeField()
    due = models.DateTimeField()


class Bid(models.Model):
    auction_id = models.IntegerField()
    user_id = models.IntegerField()
    price = models.FloatField()
    time = models.DateTimeField()