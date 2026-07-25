from django.urls import path

from movies import views


app_name = 'movies'

urlpatterns = [
    path('', views.index, name='index'),
]
