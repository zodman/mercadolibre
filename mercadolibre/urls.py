__author__ = 'sergio'
from django.conf.urls import url, include
from django.contrib.auth.decorators import login_required
from .views import *

urlpatterns = [
    url(r'^autorize/', login_required(AutorizeApp.as_view()), name='meli_autorize'),
    url(r'^redirect/', login_required(Redirect.as_view()), name='meli_redirect'),
]