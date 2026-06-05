import secrets

from django.contrib.auth.models import User
from django.db import models


class GameTable(models.Model):
    """Uma mesa virtual compartilhada, pertencente a um mestre.

    O link público é `/mesa/<Slug>/`. O mestre cria várias cenas (`Map`) e
    aponta `ActiveMap` para a que está "no ar"; os jogadores sempre veem essa.
    """

    Owner = models.ForeignKey(User, on_delete=models.CASCADE)
    Name = models.CharField(max_length=120, default='Nova Mesa')
    Slug = models.SlugField(max_length=32, unique=True, db_index=True, blank=True)
    ActiveMap = models.ForeignKey(
        'Map', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='+',
    )
    UpdatedAt = models.DateTimeField(auto_now=True)  # sinal de versão p/ polling
    CreatedAt = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-UpdatedAt', 'CreatedAt')

    def save(self, *args, **kwargs):
        if not self.Slug:
            self.Slug = secrets.token_urlsafe(16)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.Name


class Map(models.Model):
    """Uma cena dentro de uma mesa: fundo, grade e os tokens em cima dela."""

    HEX, FREE = 'hex', 'free'
    GRID_CHOICES = [
        (HEX, 'Hexagonal'),
        (FREE, 'Livre'),
    ]

    DEFAULT_WIDTH = 1600
    DEFAULT_HEIGHT = 1200

    Table = models.ForeignKey(GameTable, on_delete=models.CASCADE)
    Name = models.CharField(max_length=120, default='Novo Mapa')
    Order = models.PositiveSmallIntegerField(default=0)
    GridMode = models.CharField(max_length=8, choices=GRID_CHOICES, default=HEX)
    Background = models.ForeignKey(
        'sprites.SpriteAsset', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='tabletop_backgrounds',
    )
    WidthPx = models.PositiveIntegerField(default=DEFAULT_WIDTH)
    HeightPx = models.PositiveIntegerField(default=DEFAULT_HEIGHT)
    GridSize = models.PositiveSmallIntegerField(default=64)  # px por célula
    ShowGrid = models.BooleanField(default=True)
    CreatedAt = models.DateTimeField(auto_now_add=True)
    UpdatedAt = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('Order', 'CreatedAt')

    def __str__(self):
        return self.Name


class Token(models.Model):
    """Uma peça no mapa: mini de jogador, inimigo, NPC ou prop/marcador.

    A posição (`X`, `Y`) é o **centro** do token em px do mapa.
    """

    PLAYER, ENEMY, NPC, OBJECT = 'player', 'enemy', 'npc', 'object'
    KIND_CHOICES = [
        (PLAYER, 'Jogador'),
        (ENEMY, 'Inimigo'),
        (NPC, 'NPC'),
        (OBJECT, 'Objeto'),
    ]

    PARTY, ALLY, NEUTRAL, ENEMY_FACTION = 'party', 'ally', 'neutral', 'enemy'
    FACTION_CHOICES = [
        (PARTY, 'Grupo'),
        (ALLY, 'Aliado'),
        (NEUTRAL, 'Neutro'),
        (ENEMY_FACTION, 'Inimigo'),
    ]
    SIZE_CHOICES = [
        ('sm', 'Pequeno'),
        ('md', 'Médio'),
        ('lg', 'Grande'),
        ('xl', 'Enorme'),
    ]

    # Mapeia o Kind herdado para a facção do handoff (usado na migração e em views).
    KIND_TO_FACTION = {PLAYER: PARTY, ENEMY: ENEMY_FACTION, NPC: NEUTRAL, OBJECT: NEUTRAL}

    Map = models.ForeignKey(Map, on_delete=models.CASCADE)
    Kind = models.CharField(max_length=8, choices=KIND_CHOICES, default=ENEMY)
    Faction = models.CharField(max_length=8, choices=FACTION_CHOICES, default=ENEMY_FACTION)
    Label = models.CharField(max_length=80, blank=True)
    SpriteAsset = models.ForeignKey(
        'sprites.SpriteAsset', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='tabletop_tokens',
    )
    X = models.IntegerField(default=0)
    Y = models.IntegerField(default=0)
    HP = models.IntegerField(default=0)
    MaxHP = models.IntegerField(default=0)
    Size = models.CharField(max_length=2, choices=SIZE_CHOICES, default='md')
    Conditions = models.JSONField(default=list, blank=True)
    GridWidth = models.PositiveSmallIntegerField(default=1)   # pegada em células
    GridHeight = models.PositiveSmallIntegerField(default=1)
    MovableByPlayers = models.BooleanField(default=False)
    Hidden = models.BooleanField(default=False)  # escondido dos jogadores
    Order = models.PositiveSmallIntegerField(default=0)
    Rotation = models.PositiveSmallIntegerField(default=0)  # graus 0-345
    CreatedAt = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('Order', 'CreatedAt')

    def __str__(self):
        return self.Label or self.get_Kind_display()

    @staticmethod
    def default_movable_for_kind(kind):
        """Minis de jogador nascem movíveis por qualquer um; o resto, só pelo mestre."""
        return kind == Token.PLAYER


class FogRegion(models.Model):
    """Retângulo de névoa de guerra sobre um mapa (px do mapa)."""

    Map = models.ForeignKey(Map, on_delete=models.CASCADE)
    X = models.IntegerField(default=0)
    Y = models.IntegerField(default=0)
    Width = models.PositiveIntegerField(default=0)
    Height = models.PositiveIntegerField(default=0)
    CreatedAt = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('CreatedAt',)

    def __str__(self):
        return f'Fog {self.X},{self.Y} {self.Width}x{self.Height}'


class TerrainCell(models.Model):
    """Uma celula de terreno pintada num hexagono (coords axiais, fatia B)."""

    Map = models.ForeignKey(Map, on_delete=models.CASCADE)
    Q = models.IntegerField()
    R = models.IntegerField()
    Terrain = models.CharField(max_length=16, default='stone')
    SpriteAsset = models.ForeignKey(
        'sprites.SpriteAsset', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='tabletop_terrain',
    )
    CreatedAt = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('CreatedAt',)
        constraints = [
            models.UniqueConstraint(fields=('Map', 'Q', 'R'), name='unique_terrain_cell_per_map'),
        ]

    def __str__(self):
        return f'Terrain {self.Q},{self.R}'


class FogCell(models.Model):
    """Hex coberto por névoa (coords axiais). Substitui o FogRegion retangular."""

    Map = models.ForeignKey(Map, on_delete=models.CASCADE)
    Q = models.IntegerField()
    R = models.IntegerField()
    CreatedAt = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('CreatedAt',)
        constraints = [
            models.UniqueConstraint(fields=('Map', 'Q', 'R'), name='unique_fog_cell_per_map'),
        ]

    def __str__(self):
        return f'Fog {self.Q},{self.R}'
