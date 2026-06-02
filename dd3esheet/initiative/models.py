import secrets

from django.contrib.auth.models import User
from django.db import models


class Encounter(models.Model):
    """Um rastreador de combate compartilhado, pertencente a um mestre."""

    Owner = models.ForeignKey(User, on_delete=models.CASCADE)
    Name = models.CharField(max_length=120, default='Novo Encontro')
    Slug = models.SlugField(max_length=32, unique=True, db_index=True, blank=True)
    Round = models.PositiveIntegerField(default=1)
    ActiveCombatant = models.ForeignKey(
        'Combatant', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='+',
    )
    UpdatedAt = models.DateTimeField(auto_now=True)
    CreatedAt = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-UpdatedAt', 'CreatedAt')

    def save(self, *args, **kwargs):
        if not self.Slug:
            self.Slug = secrets.token_urlsafe(16)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.Name


class Combatant(models.Model):
    """Uma linha do rastreador: jogador, NPC ou inimigo."""

    PLAYER, NPC, ENEMY = 'player', 'npc', 'enemy'
    KIND_CHOICES = [
        (PLAYER, 'Jogador'),
        (NPC, 'NPC'),
        (ENEMY, 'Inimigo'),
    ]

    Encounter = models.ForeignKey(Encounter, on_delete=models.CASCADE)
    Name = models.CharField(max_length=80)
    Kind = models.CharField(max_length=8, choices=KIND_CHOICES, default=ENEMY)
    Initiative = models.IntegerField(default=0)
    DamageTaken = models.IntegerField(default=0)  # métrica principal: dano acumulado
    ArmorClass = models.IntegerField(null=True, blank=True)
    Effects = models.CharField(max_length=200, blank=True)
    Notes = models.CharField(max_length=300, blank=True)
    CreatedAt = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-Initiative', 'CreatedAt')

    def __str__(self):
        return self.Name
