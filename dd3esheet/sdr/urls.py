from django.urls import path
from . import views

app_name = 'sdr'

urlpatterns = [
    path("spells", views.spells, name="spells"),
    path("spell/<str:pk>", views.spell, name="spell"),
    path("monsters", views.monsters, name="monsters"),
    path("monster/<str:pk>", views.monster, name="monster"),

]
