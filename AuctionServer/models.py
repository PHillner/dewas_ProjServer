from __future__ import unicode_literals
from datetime import datetime, timedelta

from django.db import models

# Create your models here.

class Auction(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=50)
    seller = models.CharField(max_length=30)
    description = models.TextField()
    priceMin = models.FloatField()
    due = models.DateTimeField() # = datetime.now() + timedelta(min hours=72)

    @classmethod
    def getById(cls, id):
        return cls.objects.get(id=id)

    @classmethod
    def exists(cls, id):
        return len(cls.objects.filter(id=id)) > 0

    @classmethod
    def makeBet(cls, id, user_id, price, time):
        # TODO create a bet

        return 0

class User:
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=30)
    email = models.CharField(max_length=30)
    password = models.CharField(max_length=30)

    @classmethod
    def getById(cls, id):
        return cls.objects.get(id=id)

    @classmethod
    def exists(cls, id):
        return len(cls.objects.filter(id=id)) > 0

class Bet:
    id = models.IntegerField(primary_key=True)
    user_id = models.IntegerField()
    price = models.FloatField()
    time = models.DateTimeField()

    @classmethod
    def getById(cls, id):
        return cls.objects.get(id=id)