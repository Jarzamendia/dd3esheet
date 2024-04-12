from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("character/<str:pk>", views.character, name="character"),
    path("create-character/", views.createCharacter, name="create-character"),
    path("create-character2/", views.createCharacterWithDefaults, name="create-character2"),
    path("update-character/<str:pk>/", views.updateCharacter, name="update-character"),
    path("delete-character/<str:pk>/", views.deleteCharacter, name="delete-character"),

]
