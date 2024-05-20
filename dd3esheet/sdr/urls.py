from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("sdr/spells", views.spells, name="spells"),
    path("sdr/spell/<str:pk>", views.spell, name="spell"),
]
