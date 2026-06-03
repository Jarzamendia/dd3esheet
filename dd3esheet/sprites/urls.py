from django.urls import path

from . import views

app_name = 'sprites'

urlpatterns = [
    path('', views.library, name='library'),
    path('search/', views.search, name='search'),
    path('manifest/', views.manifest, name='manifest'),
    path('<slug:slug>/', views.asset_detail, name='asset-detail'),
]
