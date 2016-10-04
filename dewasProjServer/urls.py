"""dewasProjServer URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.contrib import admin
from AuctionServer.views import home
from AuctionServer.views import login
from AuctionServer.views import register
from AuctionServer.views import auction
from AuctionServer.views import auction_edit
from AuctionServer.views import new_auction
from AuctionServer.views import user
from AuctionServer.views import user_edit

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^/$', home),
    url(r'^login/$', login),
    url(r'^register/$', register),
    url(r'^auction/id/(?P<id>\d+)/$', auction),
    url(r'^auction/id/(?P<id>\d+)/edit/$', auction_edit),
    url(r'^auction/new/', new_auction),
    url(r'^user/id/(?P<id>\d+)/$', user),
    url(r'^user/id/(?P<id>\d+)/edit/$', user_edit),
]
