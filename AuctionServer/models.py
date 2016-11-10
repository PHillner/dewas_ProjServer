from __future__ import unicode_literals
from django.core.mail import send_mail

from django.db import models
from django.contrib.auth.models import User

# Create your models here.


class Auction(models.Model):
    name = models.CharField(max_length=50)
    seller = models.ForeignKey(User,on_delete=models.CASCADE)
    description = models.TextField()
    priceMin = models.DecimalField(decimal_places=2, max_digits=28)
    time = models.DateTimeField()
    due = models.DateTimeField()
    a_hash = models.TextField()
    resolved = models.BooleanField()
    banned = models.BooleanField()

    def confirmation_email(self):
        send_mail('Your auction has been created.',
                  'Your auction "' + self.name + '" (id: ' + str(self.id) + ') has been created.',
                  'phillner@abo.fi',
                  [self.seller.email],
                  fail_silently=False)

    def resolve(self):
        self.notify_seller()
        self.notify_winner()
        self.notify_bidders()

    def notify_seller(self):
        if len(Bid.objects.filter(auction=self.id)) > 0:
            bid = Bid.objects.filter(auction=self.id).order_by("price").last()
            send_mail('Your auction has ended with a buyer!',
                      'Congratulations!\nYour auction "' + self.name + '" (id: ' + self.id + ')'
                                 ' has ended and found a buyer!\nYour auction sold for ' + bid.price + ' EUR.',
                      'phillner@abo.fi',
                      [self.seller.email],
                      fail_silently=False)
        else:
            send_mail('Your auction has ended without a buyer.',
                      'Your auction "' + self.name + '" (id: ' + self.id + ') has ended without finding a buyer.\n',
                      'phillner@abo.fi',
                      [self.seller.email],
                      fail_silently=False)

    def notify_winner(self):
        if len(Bid.objects.filter(auction=self.id)) > 0:
            bid = Bid.objects.filter(auction=self.id).order_by("price").last()
            send_mail('Your bid has won',
                      'Congratulations!\nYour bid in auction "'+self.name+'" (id: '+self.id+') has won!\n'
                                    'You bidded for '+bid.price+' EUR.',
                      'phillner@abo.fi',
                      [bid.bidder.email],
                      fail_silently=False)

    def notify_bidders(self):
        if len(Bid.objects.filter(auction=self.id)) > 1:
            win_bid = bid = Bid.objects.filter(auction=self.id).order_by("price").last()
            bidders = Bid.objects.filter(auction=self.id).values_list("bidder", flat=True).distinct()
            for bidder in bidders:
                if bidder.id is not win_bid.id:
                    send_mail('Your bid has lost',
                              'Your bid in auction "'+self.name+'" (id: '+self.id+') was out-bidded.',
                              'phillner@abo.fi',
                              [bidder.email],
                              fail_silently=False)

    def new_bid_notify(self):
        bids = Bid.objects.filter(auction=self.id).order_by("price")
        if len(bids) > 0:
            for bid in bids:
                send_mail('An auction you have bid on has a new top.',
                          'An auction you have bid on "' + self.name + '" (id: ' + self.id +
                          ') has a new bid of ' + str(bids.last().price) + ' EUR.\n',
                          'phillner@abo.fi',
                          [self.seller.email],
                          fail_silently=False)

        send_mail('Your auction has a new bid.',
                  'Your auction "' + self.name + '" (id: ' + self.id + ') has a new bid of '+str(bids.last().price)+' EUR.\n',
                  'phillner@abo.fi',
                  [self.seller.email],
                  fail_silently=False)


class Bid(models.Model):
    auction = models.ForeignKey(Auction, on_delete=models.CASCADE)
    bidder = models.ForeignKey(User, on_delete=models.CASCADE)
    price = models.DecimalField(decimal_places=2, max_digits=28)
    time = models.DateTimeField()
