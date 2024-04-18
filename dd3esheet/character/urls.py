from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("character/<str:pk>", views.character, name="character"),
    path("create-character/", views.createCharacter, name="create-character"),
    path("delete-character/<str:pk>/", views.deleteCharacter, name="delete-character"),

]
