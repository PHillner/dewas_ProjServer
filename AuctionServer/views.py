from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, render_to_response, redirect
from django.http import HttpResponseRedirect
from django.views.decorators.csrf import csrf_protect
from datetime import datetime, timedelta
from django.contrib import messages
from models import Auction, Bid
from django.contrib.auth import authenticate
from decimal import *
from background_task import background

salt = "brumm"

# Create your views here.


def update_session_stats(request, page):
    if "session_start" not in request.session:
        request.session["session_start"] = datetime.now().strftime('%b %m, %Y, %I:%M %p')
        request.session["visited"] = 0
        request.session["created"] = 0
        request.session["deleted"] = 0
        request.session["bidded"] = 0

    if page == 'auction':
        request.session["visited"] += 1
    elif page == 'auction_new':
        request.session["created"] += 1
    elif page == 'auction_delete':
        request.session["deleted"] += 1
    elif page == 'bid':
        request.session["bidded"] += 1


def session_stats_reset(request):
    request.session.flush()
    update_session_stats(request, request.POST.get("next"))
    messages.add_message(request, messages.INFO, "Session has been reset.")
    return redirect(request.POST.get("next"))


def home(request):
    update_session_stats(request, 'home')
    auctions = Auction.objects.all().filter().order_by("time").reverse()
    return render(request, 'home.html', {'auctions': auctions})


@csrf_protect
def register(request):
    if request.method == "POST" and not request.user.is_authenticated:
        if str(request.POST['username']) is None or str(request.POST['username']) is ''\
                or str(request.POST['password']) is None or str(request.POST['password']) is ''\
                or str(request.POST['password_check']) is None or str(request.POST['password_check']) is '':
            messages.add_message(request,
                                 messages.ERROR,
                                 "You need to fill at least the username and password fields to register.")
            return render(request, 'register.html', register_context(request))
        elif str(request.POST['password']) != str(request.POST['password_check']):
            messages.add_message(request, messages.ERROR, "Passwords must match!")
            return render(request, 'register.html', register_context(request))
        else:
            user = authenticate(username=request.POST.get("username"))
            if user is not None:
                messages.add_message(request, messages.ERROR, "Unable to register to given credentials.\n"
                                                              "Try other username.")
                return render(request, 'register.html', register_context(request))
            else:
                uname = str(request.POST['username'])
                passw = str(request.POST['password'])
                user = User.objects.create_user(uname, password=passw)
                if user is None:
                    messages.add_message(request, messages.ERROR, "Registration failed.")
                    return render(request, 'register.html', register_context(request))
                user.first_name = str(request.POST['first_name'])
                user.last_name = str(request.POST['last_name'])
                user.email = str(request.POST['email'])
                messages.add_message(request, messages.INFO, "Registration successful!")
                return render(request, 'home.html')

    elif request.method == "GET" and not request.user.is_authenticated:
        return render(request, 'register.html', {'fname': '',
                                                         'lname': '',
                                                         'email': '',
                                                         'uname': ''})
    else:
        messages.add_message(request, messages.WARNING, "You can't do that.")
        if request.POST.get("next") is not None:
            return redirect(request.POST.get("next"))
        else:
            return HttpResponseRedirect('/')


@login_required(login_url="/login/")
def user(request):
    if request.user.is_authenticated:
        user_id = request.user.id
        return render(request, 'user.html',
                      {'user': User.objects.get(id=user_id),
                       'auctions': Auction.objects.filter(seller=user_id).order_by("time").reverse(),
                       'bids': Bid.objects.filter(bidder=user_id).order_by("time").reverse()})
    else:
        messages.add_message(request, messages.ERROR, "User not found.")
        if request.POST.get("next") is not None:
            return redirect(request.POST.get("next"))
        else:
            return HttpResponseRedirect('/')


@login_required(login_url="/login/")
@csrf_protect
def user_edit(request):
    if request.user.is_authenticated:
        user = User.objects.get(id=request.user.id)
    else:
        messages.add_message(request, messages.WARNING, "You can't do that.")
        if request.POST.get("next") is not None:
            return redirect(request.POST.get("next"))
        else:
            return HttpResponseRedirect('/')
    if request.method == "POST" and "userName" in request.POST:
        user.username = request.POST["userName"]
        user.email = request.POST["email"]
        if request.POST["password"] != "":
            user.password = request.POST["password"]
        user.save()
        return HttpResponseRedirect('/user/')
    else:
        return render_to_response("user_edit.html", {'user': user})


def auction(request, id):
    if len(Auction.objects.filter(id=id)) > 0:
        auction = Auction.objects.get(id=id)
        update_session_stats(request, 'auction')
    else:
        messages.add_message(request, messages.ERROR, "Auction not found.")
        if request.POST.get("next") is not None:
            return redirect(request.POST.get("next"))
        else:
            return HttpResponseRedirect('/')
    return render(request, 'auction.html',
                  {'auction': auction,
                   'bids': Bid.objects.filter(auction=auction).order_by("time").reverse()})


@login_required(login_url="/login/")
@csrf_protect
def auction_new(request):
    if request.method == "POST" and request.POST.get("choice1"):
        getcontext().prec = 2
        auction = Auction()
        auction.seller = request.user
        auction.name = request.POST["name"]
        auction.description = request.POST["description"]
        auction.priceMin = Decimal(request.POST["priceMin"])
        auction.time = datetime.now()
        delta = int(request.POST["dateEnd"])
        auction.due = datetime.now() + timedelta(hours=delta)
        auction.a_hash = hash(auction.name + auction.description + str(auction.due) + str(auction.priceMin) + salt)
        auction.save()
        auction.confirmation_email()
        update_session_stats(request, 'auction_new')
        messages.add_message(request, messages.SUCCESS, "Auction created")
        return HttpResponseRedirect('/auction/'+str(auction.id)+'/')
    elif request.method == "POST":
        auction = Auction()
        auction.name = request.POST["name"]
        auction.description = request.POST["description"]
        auction.priceMin = Decimal(request.POST["priceMin"])
        delta = int(request.POST["dateEnd"])

        if auction.priceMin.as_tuple().exponent == -2:
            messages.add_message(request, messages.ERROR, "You have to give the starting price with 2 decimals.")

        if delta < 72:
            messages.add_message(request, messages.ERROR, "Auction due time must be at least 72 hours in the future.")

        if len(messages.get_messages(request)) > 0:
            return render(request, "auction_new.html", {'auction': auction})

        auction.due = datetime.now() + timedelta(hours=delta)
        return render(request, "auction_new_confirm.html", {'auction': auction})
    else:
        return render(request, "auction_new.html")


@login_required(login_url="/login/")
@csrf_protect
def auction_delete(request, id):
    if request.method == "POST"\
            and request.POST.get("choice1")\
            and request.user.id == Auction.objects.get(id=id).seller:
        auction = Auction.objects.get(id=id)
        auction.delete()
        update_session_stats(request, 'auction_delete')
        messages.add_message(request, messages.SUCCESS, "Blog post removed")
        return HttpResponseRedirect('/')
    else:
        return render(request, 'auction_delete.html', {'auction': Auction.objects.get(id=id)})


@login_required(login_url="/login/")
@csrf_protect
def auction_edit(request, id):
    if request.user.is_authenticated and len(Auction.objects.filter(id=id)) > 0:
        auction = Auction.objects.get(id=id)
        if request.user.id is not auction.seller:
            messages.add_message(request, messages.WARNING, "You can't do that.")
            if request.POST.get("next") is not None:
                return redirect(request.POST.get("next"))
            else:
                return HttpResponseRedirect('/')
    else:
        messages.add_message(request, messages.ERROR, "Auction not found.")
        if request.POST.get("next") is not None:
            return redirect(request.POST.get("next"))
        else:
            return HttpResponseRedirect('/')
    if request.method == "POST" and "description" in request.POST:
        auction.name = request.POST["name"]
        auction.description = request.POST["description"]
        if len(Bid.objects.filter(auction_id=id)) > 0:
            auction.a_hash = hash(auction.name + auction.description + str(auction.due) +\
                             str(Bid.objects.filter(auction_id=id).order_by("price").first().price) + salt)
        else:
            auction.a_hash = hash(auction.name + auction.description + str(auction.due) + str(auction.priceMin) + salt)
        auction.save()
        return HttpResponseRedirect('/auction/'+auction.id)
    else:
        return render(request, "auction_edit.html",
                      {'auction': auction, 'bids': Bid.objects.filter(auction_id=id)})


def ban(request, id):
    if not Auction.objects.get(id=id).resolved\
            and request.method == "POST"\
            and request.POST.get("choice1")\
            and request.user.is_superuser:
        auction = Auction.objects.get(id=id)
        auction.banned = True
        auction.a_hash = hash(auction.name + auction.description + str(auction.due) + str(auction.priceMin) + salt)
        auction.save()
        messages.add_message(request, messages.SUCCESS, "Auction banned")
        return HttpResponseRedirect('/auction/'+id)
    elif request.method == "POST"\
            and request.POST.get("choice2")\
            and request.user.is_superuser:
        return HttpResponseRedirect('/auction/' + id)
    else:
        return render(request, 'auction_ban.html', {'auction': Auction.objects.get(id=id)})


def bid(request, id):
    if request.method == "POST"\
                and len(Auction.objects.filter(id=id)) > 0\
                and request.user is not Auction.objects.get(id=id).seller\
                and not Auction.objects.get(id=id).resolved\
                and not Auction.objects.get(id=id).banned:
        getcontext().prec = 2
        auction = Auction.objects.get(id=id)
        bid = Bid()
        bid.auction = auction
        bid.bidder = request.user
        price = Decimal(request.POST["price"])
        bids = Bid.objects.filter(auction_id=auction).order_by("price")
        if bids.last().bidder.id is request.user.id:
            messages.add_message(request, messages.ERROR,
                                 "You already have the highest bid!")
            if request.POST.get("next") is not None:
                return redirect(request.POST.get("next"))
            else:
                return HttpResponseRedirect('/auction/' + id + '/')

        if len(bids) > 0 and price > bids.last().price and price.as_tuple().exponent == -2:
            bid.price = price
        elif price >= auction.priceMin and price.as_tuple().exponent == -2:
            bid.price = price
        else:
            messages.add_message(request,messages.ERROR,
                                 "The bid must exceed the minimum price or the highest bid, whichever is higher, "
                                 "by at least 0.01 (always use 2 decimals).")
            if request.POST.get("next") is not None:
                return redirect(request.POST.get("next"))
            else:
                return HttpResponseRedirect('/auction/'+id+'/')
        bid.time = datetime.now()
        if auction.a_hash != Auction.objects.get(id=id).a_hash:
            messages.add_message(request, messages.ERROR,
                                 "The auction has either been edited or a new bid has been made since last time the "
                                 "page was loaded. Please try bidding again.")
            return redirect('/auction/'+id+'/')
        bid.save()
        auction.a_hash = hash(auction.name + auction.description + str(auction.due) +
                              str(Bid.objects.filter(auction_id=id).order_by("price").first().price) + salt)
        auction.save()
        update_session_stats(request, "bid")
        messages.add_message(request, messages.INFO, "Bid created")
        return redirect(request.POST.get("next"))


def search(request):
    if request.method == "POST" and request.POST["search_menu"] is not "" and len(Auction.objects.filter(id=id)) > 0:
        if request.POST["search_menu"] == "name":
            auction = Auction.objects.filter(name__contains=request.POST["search_variable"])\
                .order_by("time").reverse()
        elif request.POST["search_menu"] == "desc":
            auction = Auction.objects.filter(description__contains=request.POST["search_variable"])\
                .order_by("time").reverse()
        elif request.POST["search_menu"] == "above":
            auction = Auction.objects.filter(priceMin__gt=Decimal(request.POST["search_variable"]))\
                .order_by("time").reverse()
        elif request.POST["search_menu"] == "below":
            auction = Auction.objects.filter(priceMin__lt=Decimal(request.POST["search_variable"]))\
                .order_by("time").reverse()
        return render(request, "search.html", {'results': auction, 'search_variable': request.POST["search_variable"]})
    else:
        return render(request, "search.html")


def register_context(request):
    return {'fname': str(request.POST['first_name']),
            'lname': str(request.POST['last_name']),
            'email': str(request.POST['email']),
            'uname': str(request.POST['username'])}


# does actually nothing, would have otherwise resolved auctions
@background()
def resolve_auction(repeat=10, repeat_until=None):
    if len(Auction.objects.filter(id=id)) > 0:
        for auction in Auction.objects.filter(due__gt=datetime.now()-timedelta(seconds=20)).order_by("time"):
            if not auction.resolved and not auction.banned:
                auction.resolved = True
                auction.a_hash = hash(auction.name + auction.description + str(auction.due) + str(auction.priceMin) + salt)
                auction.save()
                auction.resolve()
