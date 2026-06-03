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

    SQUARE, FREE = 'square', 'free'
    GRID_CHOICES = [
        (SQUARE, 'Quadrada'),
        (FREE, 'Livre'),
    ]

    DEFAULT_WIDTH = 1600
    DEFAULT_HEIGHT = 1200

    Table = models.ForeignKey(GameTable, on_delete=models.CASCADE)
    Name = models.CharField(max_length=120, default='Novo Mapa')
    Order = models.PositiveSmallIntegerField(default=0)
    GridMode = models.CharField(max_length=8, choices=GRID_CHOICES, default=SQUARE)
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

    Map = models.ForeignKey(Map, on_delete=models.CASCADE)
    Kind = models.CharField(max_length=8, choices=KIND_CHOICES, default=ENEMY)
    Label = models.CharField(max_length=80, blank=True)
    SpriteAsset = models.ForeignKey(
        'sprites.SpriteAsset', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='tabletop_tokens',
    )
    X = models.IntegerField(default=0)
    Y = models.IntegerField(default=0)
    GridWidth = models.PositiveSmallIntegerField(default=1)   # pegada em células
    GridHeight = models.PositiveSmallIntegerField(default=1)
    MovableByPlayers = models.BooleanField(default=False)
    Hidden = models.BooleanField(default=False)  # escondido dos jogadores
    Order = models.PositiveSmallIntegerField(default=0)
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
