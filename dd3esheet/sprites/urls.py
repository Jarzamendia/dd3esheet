from django.urls import path

from . import views

app_name = 'sprites'

urlpatterns = [
    path('search/', views.search, name='search'),
    path('manifest/', views.manifest, name='manifest'),
]
