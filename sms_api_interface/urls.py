from django.urls import path
from . import views
urlpatterns = [
    path('', views.home, name='smsApi_home'),
]
