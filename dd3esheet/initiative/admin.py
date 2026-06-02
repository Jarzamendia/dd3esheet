from django.contrib import admin

from .models import Combatant, Encounter

admin.site.register(Encounter)
admin.site.register(Combatant)
