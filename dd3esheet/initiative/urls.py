from django.urls import path

from . import views

app_name = 'initiative'

urlpatterns = [
    path('', views.home, name='home'),
    path('novo', views.create_encounter, name='create-encounter'),

    path('<slug:slug>/', views.board, name='board'),
    path('<slug:slug>/fragment', views.board_fragment, name='board-fragment'),

    path('<slug:slug>/combatente/add', views.add_combatant, name='add-combatant'),
    path('<slug:slug>/combatente/<int:cid>/edit', views.edit_combatant, name='edit-combatant'),
    path('<slug:slug>/combatente/<int:cid>/damage', views.apply_damage, name='apply-damage'),
    path('<slug:slug>/combatente/<int:cid>/delete', views.delete_combatant, name='delete-combatant'),

    path('<slug:slug>/turn/next', views.next_turn, name='next-turn'),
    path('<slug:slug>/turn/reset', views.reset_turn, name='reset-turn'),
]
