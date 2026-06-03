from django.contrib import admin

from .models import FogRegion, GameTable, Map, Token

admin.site.register(GameTable)
admin.site.register(Map)
admin.site.register(Token)
admin.site.register(FogRegion)
