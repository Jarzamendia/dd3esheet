from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    path('', include('home.urls')),
    path('character/', include('character.urls')),
    path('sdr/', include('sdr.urls')),
    path('iniciativa/', include('initiative.urls')),
]
