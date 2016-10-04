from django.shortcuts import render, get_object_or_404, render_to_response
from django.http import HttpResponse, HttpResponseRedirect
from django.template import Template, Context, RequestContext
from django.template.loader import get_template
from models import Auction
from models import User

# Create your views here.
siteName = "AuctionHouse 9000 - "


def home(request):
    t = get_template(home.html)
    html = t.render(Context({'siteName': siteName,'name': "Home"}))
    return HttpResponse(html)

def login(request):
    t = get_template(login.html)
    html = t.render(Context({'siteName': siteName,'name': "Login"}))
    return HttpResponse(html)

def register(request):
    t = get_template(register.html)
    html = t.render(Context({'siteName': siteName,'name': "Register"}))
    return HttpResponse(html)

def auction(request,id):
    if Auction.exists(id):
        auction = Auction.getById(id)
    else:
        return None
    t = get_template(auction.html)
    html = t.render(Context(
        {'siteName': siteName,'id':auction.id,'name': auction.name,'description': auction.description,
         'priceMin': auction.priceMin,'seller': auction.seller,'due': auction.due})) # TODO add list of 'bets'
    return HttpResponse(html)


def auction_edit(request):
    if Auction.exists(id):
        auction = Auction.getById(id)
    else:
        return None

    if request.method == "POST" and request.POST.has_key("description"):
        auction.description = request.POST["description"]
        auction.save()
        return HttpResponseRedirect('/auction/'+auction.id)
    else:
        return render_to_response("auction_edit.html",
                    {'siteName': siteName,'name': auction.name,'description': auction.description},
                                  context_instance = RequestContext(request))


def user(request, id):
    if User.exists(id):
        user = User.getById(id)
    else:
        return None
    t = get_template(user.html)
    html = get_template(user_edit.html)


def user_edit(request):
    if User.exists(id):
        user = Auction.getById(id)
    else:
        return None

    if request.method == "POST" and request.POST.has_key("userName"):
        user.userName = request.POST["userName"]
        user.email = request.POST["email"]
        user.password = request.POST["password"]
        user.save()
        return HttpResponseRedirect('/auction/'+user.id)
    else:
        return render_to_response("auction_edit.html",
                                  {'siteName': siteName,'name': "User",'userName': user.userName},
                                  context_instance = RequestContext(request))


def new_auction(request):
    t = get_template(new_auction.html)
    html = t.render(Context({'siteName': siteName,'name': "New auction"}))
    return HttpResponse(html)