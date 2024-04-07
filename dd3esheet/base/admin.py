from django.contrib import admin

from .models import Character
from .models import CharacterDescription
from .models import CharacterStats
from .models import CharacterStatus
from .models import CharacterSavingThrows
from .models import CharacterAttackModifiers
from .models import CharacterWeapon
from .models import CharacterSkillGraduation
from .models import CharacterSkill
from .models import CharacterArmor
from .models import CharacterShield
from .models import CharacterProtectionItem
from .models import CharacterOtherItem
from .models import CharacterOtherItemObs
from .models import CharacterMoney
from .models import CharacterFeat
from .models import CharacterAbility
from .models import CharacterSpell
from .models import CharacterSpellSave
from .models import CharacterArcaneSpellFailCheck
from .models import CharacterMagicConditionalModifiers
from .models import CharacterMagicDayUse
from .models import CharacterLanguages

admin.site.register(Character)
admin.site.register(CharacterDescription)
admin.site.register(CharacterStats)
admin.site.register(CharacterStatus)
admin.site.register(CharacterSavingThrows)
admin.site.register(CharacterAttackModifiers)
admin.site.register(CharacterWeapon)
admin.site.register(CharacterSkillGraduation)
admin.site.register(CharacterSkill)
admin.site.register(CharacterArmor)
admin.site.register(CharacterShield)
admin.site.register(CharacterProtectionItem)
admin.site.register(CharacterOtherItem)
admin.site.register(CharacterOtherItemObs)
admin.site.register(CharacterMoney)
admin.site.register(CharacterFeat)
admin.site.register(CharacterAbility)
admin.site.register(CharacterSpell)
admin.site.register(CharacterSpellSave)
admin.site.register(CharacterArcaneSpellFailCheck)
admin.site.register(CharacterMagicConditionalModifiers)
admin.site.register(CharacterMagicDayUse)
admin.site.register(CharacterLanguages)
