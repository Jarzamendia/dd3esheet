from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    path('', include('home.urls')),
    path('sprites/', include('sprites.urls')),
    path('character/', include('character.urls')),
    path('sdr/', include('sdr.urls')),
    path('iniciativa/', include('initiative.urls')),
    path('mesa/', include('tabletop.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
