from django.urls import path
from . import views

app_name = 'character'

urlpatterns = [
    path("", views.home, name="home"),
    path("character/<int:pk>", views.character, name="character"),
    path("character/<int:pk>/companions", views.companions, name="companions"),
    path("character/<int:pk>/summons/search/", views.summon_search, name="summon-search"),
    path("character/<int:pk>/summons/<int:summon_id>/toggle-highlight/", views.toggle_summon_highlight, name="toggle-summon-highlight"),
    path("character/<int:pk>/summons/from-monster/<int:monster_id>/", views.create_summon_from_monster, name="create-summon-from-monster"),
    path("character/<int:pk>/spellbook", views.spellbook, name="spellbook"),
    path("character/<int:pk>/daily-resources", views.dailyResources, name="daily-resources"),
    path("character/<int:pk>/reputation", views.reputation, name="reputation"),
    path("character/<int:pk>/spell-slot/<int:slot_id>/toggle/", views.toggleSpellSlot, name="toggle-spell-slot"),
    path("character/<int:pk>/spell/<int:sdr_id>/", views.spell_detail, name="spell-detail"),
    path("create-character/", views.createCharacter, name="create-character"),
    path("delete-character/<int:pk>/", views.deleteCharacter, name="delete-character"),

]
