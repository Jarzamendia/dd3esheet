from django.urls import path
from . import views

app_name = 'character'

urlpatterns = [
    path("", views.home, name="home"),
    path("character/<str:pk>", views.character, name="character"),
    path("character/<str:pk>/spell-slot/<int:slot_id>/toggle/", views.toggleSpellSlot, name="toggle-spell-slot"),
    path("create-character/", views.createCharacter, name="create-character"),
    path("delete-character/<str:pk>/", views.deleteCharacter, name="delete-character"),

]
