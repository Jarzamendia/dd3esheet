from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('home.urls')),
    path('character/', include('character.urls')),
    path('sdr/', include('sdr.urls'))
]
