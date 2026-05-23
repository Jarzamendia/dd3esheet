from django.urls import path
from . import views

app_name = 'sdr'

urlpatterns = [
    path('', views.home, name='home'),

    path('spells/', views.spells, name='spells'),
    path('spell/<str:pk>/', views.spell, name='spell'),

    path('monsters/', views.monsters, name='monsters'),
    path('monster/<str:pk>/', views.monster, name='monster'),

    path('classes/', views.classes, name='classes'),
    path('class/<str:pk>/', views.dnd_class, name='class'),

    path('domains/', views.domains, name='domains'),
    path('domain/<str:pk>/', views.domain, name='domain'),

    path('equipment/', views.equipment_list, name='equipment'),
    path('equipment/<str:pk>/', views.equipment, name='equipment_detail'),

    path('feats/', views.feats, name='feats'),
    path('feat/<str:pk>/', views.feat, name='feat'),

    path('items/', views.items, name='items'),
    path('item/<str:pk>/', views.item, name='item'),

    path('powers/', views.powers, name='powers'),
    path('power/<str:pk>/', views.power, name='power'),

    path('skills/', views.skills, name='skills'),
    path('skill/<str:pk>/', views.skill, name='skill'),
]
