from django.urls import path
from . import views

app_name = 'character'

urlpatterns = [
    path("", views.home, name="home"),
    path("character/<int:pk>", views.character, name="character"),
    path("character/<int:pk>/companions", views.companions, name="companions"),
    path("character/<int:pk>/daily-resources", views.dailyResources, name="daily-resources"),
    path("character/<int:pk>/reputation", views.reputation, name="reputation"),
    path("character/<int:pk>/spell-slot/<int:slot_id>/toggle/", views.toggleSpellSlot, name="toggle-spell-slot"),
    path("create-character/", views.createCharacter, name="create-character"),
    path("delete-character/<int:pk>/", views.deleteCharacter, name="delete-character"),

]
