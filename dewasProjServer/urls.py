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
from django.contrib.auth import views as auth_views
from AuctionServer.views import *

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^$', home, name='home'),
    #url(r'^login/$', login),
    url(r'^register/$', register),
    url(r'^auction/(?P<id>\d+)/$', auction),
    url(r'^auction/new/$', auction_new),
    url(r'^auction/new/confirm$', auction_new),
    url(r'^auction/(?P<id>\d+)/edit/$', auction_edit),
    url(r'^auction/(?P<id>\d+)/delete/$', auction_delete),
    url(r'^bid/(?P<id>\d+)/$', bid, name='bid'),
    url(r'^user/$', user),
    url(r'^user/edit/$', user_edit),
    url(r'^login/$', auth_views.login, name='login'),
    url(r'^logout/$', auth_views.logout, name='logout'),
    url(r'^search/$', search),
    url(r'^auction/(?P<id>\d+)/ban/$', ban),
    url(r'^session_stats_reset/$', session_stats_reset),
]
