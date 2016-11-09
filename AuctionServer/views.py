from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, render_to_response, redirect
from django.http import HttpResponseRedirect
from django.template import Context
from django.views.decorators.csrf import csrf_protect
from datetime import datetime, timedelta
from django.contrib import messages
from models import Auction, Bid
from django.contrib.auth import authenticate, login, logout

salt = "brumm"

# Create your views here.


def update_session_stats(request, page):
    if "session_start" not in request.session:
        request.session["session_start"] = datetime.now().strftime('%b %m, %Y, %I:%M %p')
        request.session["visited"] = 0
        request.session["created"] = 0
        request.session["deleted"] = 0
        request.session["user_id"] = 0

    if page == 'auction':
        request.session["visited"] += 1
    elif page == 'auction_new':
        request.session["created"] += 1
    elif page == 'auction_delete':
        request.session["deleted"] += 1


def session_stats_reset(request):
    request.session.flush()
    update_session_stats(request, request.POST.get("next"))
    messages.add_message(request, messages.INFO, "Session statistics has been reset.")
    return redirect(request.POST.get("next"))


def home(request):
    update_session_stats(request, 'home')
    return render(request, 'home.html', Context({'auctions': Auction.objects.order_by("time").reverse()}))


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
        return render(request, 'register.html', Context({'fname': '',
                                                         'lname': '',
                                                         'email': '',
                                                         'uname': ''}))
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
        return render(request, 'user.html', Context({
            'user': User.objects.get(id=user_id),
            'auctions': Auction.objects.filter(seller=user_id).order_by("time").reverse(),
            'bids': Bid.objects.filter(bidder=user_id).order_by("time").reverse()}))
    else:
        messages.add_message(request, messages.ERROR, "User not found.")
        if request.POST.get("next"):
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
        return render_to_response("user_edit.html", Context({'user': user}))


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
    return render(request, 'auction.html', Context({'auction': auction, 'bids': Bid.objects.filter(auction=auction).order_by("time").reverse()}))


@login_required(login_url="/login/")
@csrf_protect
def auction_new(request):
    if request.method == "POST":
        auction = Auction()
        auction.seller = request.user
        auction.name = request.POST["name"]
        auction.description = request.POST["description"]
        auction.priceMin = request.POST["priceMin"]
        auction.time = datetime.now()
        delta = int(request.POST["dateEnd"])
        if delta < 72:
            messages.add_message(request, messages.ERROR, "Auction due time must be at least 72 hours in the future.")
            return render(request, "auction_new.html", Context({'auction': auction}))
        auction.due = datetime.now() + timedelta(hours=delta)
        auction.a_hash = hash(auction.name + auction.description + str(auction.due) + auction.priceMin + salt)
        auction.save()
        update_session_stats(request, 'auction_new')
        messages.add_message(request, messages.SUCCESS, "Auction created")
        return HttpResponseRedirect('/auction/'+str(auction.id)+'/')
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
        return render(request, 'auction_delete.html', Context({'auction': Auction.objects.get(id=id)}))


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
                             Bid.objects.filter(auction_id=id).order_by("price") + salt)
        else:
            auction.a_hash = hash(auction.name + auction.description + str(auction.due) + auction.priceMin + salt)
        auction.save()
        return HttpResponseRedirect('/auction/'+auction.id)
    else:
        return render(request, "auction_edit.html",
                      Context({'auction': auction, 'bids': Bid.objects.filter(auction_id=id)}))


def bid(request, id):
    if request.method == "POST"\
            and len(Auction.objects.filter(id=id)) > 0\
            and request.user is not Auction.objects.get(id=id).seller:
        auction = Auction.objects.get(id=id)
        bid = Bid()
        bid.auction = auction
        bid.bidder = request.user
        price = float(request.POST["price"])
        bids = Bid.objects.filter(auction_id=auction).order_by("price")
        if len(bids) > 0 and price > bids.last():
            bid.price = price
        elif price > auction.priceMin:
            bid.price = price
        else:
            messages.add_message(request,messages.ERROR,
                             "The bid must exceed the minimum price or the highest bid by 0.01, whichever is higher.")
            if request.POST.get("next") is not None:
                return redirect(request.POST.get("next"))
            else:
                return HttpResponseRedirect('/auction/'+id+'/')
        bid.time = datetime.now()
        bid.save()
        auction.a_hash = hash(auction.name + auction.description + str(auction.due) + \
                              str(Bid.objects.filter(auction_id=id).order_by("price").first().price) + salt)
        auction.save()
        messages.add_message(request, messages.INFO, "Bid created")
        return redirect(request.POST.get("next"))



def register_context(request):
    return Context({'fname': str(request.POST['first_name']),
                    'lname': str(request.POST['last_name']),
                    'email': str(request.POST['email']),
                    'uname': str(request.POST['username'])})
