from django.urls import path

from . import views

app_name = 'tabletop'

urlpatterns = [
    path('', views.home, name='home'),
    path('novo', views.create_table, name='create-table'),

    path('<slug:slug>/', views.table_view, name='table'),
    path('<slug:slug>/fragment', views.live_fragment, name='live-fragment'),
    path('<slug:slug>/manage', views.manage, name='manage'),

    path('<slug:slug>/map/add', views.add_map, name='add-map'),
    path('<slug:slug>/map/<int:mid>/edit', views.edit_map, name='edit-map'),
    path('<slug:slug>/map/<int:mid>/delete', views.delete_map, name='delete-map'),
    path('<slug:slug>/map/<int:mid>/activate', views.set_active, name='set-active'),
    path('<slug:slug>/map/<int:mid>/editor', views.editor, name='editor'),
    path('<slug:slug>/map/<int:mid>/scene/save', views.scene_save, name='scene-save'),
    path('<slug:slug>/map/<int:mid>/fog/add', views.add_fog, name='add-fog'),
    path('<slug:slug>/map/<int:mid>/terrain/paint', views.paint_terrain, name='paint-terrain'),
    path('<slug:slug>/map/<int:mid>/terrain/clear', views.clear_terrain, name='clear-terrain'),

    path('<slug:slug>/token/add', views.add_token, name='add-token'),
    path('<slug:slug>/token/<int:tid>/edit', views.edit_token, name='edit-token'),
    path('<slug:slug>/token/<int:tid>/delete', views.delete_token, name='delete-token'),
    path('<slug:slug>/token/<int:tid>/move', views.move_token, name='move-token'),

    path('<slug:slug>/fog/<int:fid>/delete', views.delete_fog, name='delete-fog'),
]
