import hashlib
from pathlib import Path

from django.conf import settings
from django.core.validators import FileExtensionValidator, MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q
from django.utils.text import slugify


IMAGE_EXTENSIONS = ('png', 'jpg', 'jpeg', 'webp', 'gif', 'svg')


def _safe_file_stem(filename):
    stem = slugify(Path(filename).stem)[:60]
    return stem or 'sprite'


def sprite_upload_path(instance, filename):
    ext = Path(filename).suffix.lower()
    category = slugify(instance.Category or SpriteAsset.GENERIC) or SpriteAsset.GENERIC
    return f'sprites/original/{category}/{_safe_file_stem(filename)}{ext}'


def sprite_variant_upload_path(instance, filename):
    ext = Path(filename).suffix.lower()
    category = slugify(instance.SpriteAsset.Category or SpriteAsset.GENERIC) or SpriteAsset.GENERIC
    return f'sprites/variants/{category}/{_safe_file_stem(filename)}{ext}'


def file_checksum(file_obj):
    digest = hashlib.sha256()
    position = None
    try:
        position = file_obj.tell()
    except (AttributeError, OSError):
        position = None
    try:
        file_obj.seek(0)
    except (AttributeError, OSError):
        pass
    for chunk in file_obj.chunks():
        digest.update(chunk)
    if position is not None:
        try:
            file_obj.seek(position)
        except (AttributeError, OSError):
            pass
    return digest.hexdigest()


class SpriteAssetQuerySet(models.QuerySet):
    def active(self):
        return self.filter(IsActive=True)

    def visible_to(self, user):
        public = Q(Visibility=SpriteAsset.PUBLIC)
        if user is not None and user.is_authenticated:
            return self.filter(public | Q(Owner=user))
        return self.filter(public)


class SpriteAsset(models.Model):
    CLASS = 'class'
    MONSTER = 'monster'
    CHARACTER = 'character'
    COMPANION = 'companion'
    MAP_TOKEN = 'map_token'
    MAP_TILE = 'map_tile'
    ITEM = 'item'
    GENERIC = 'generic'

    CATEGORY_CHOICES = (
        (CLASS, 'Classe'),
        (MONSTER, 'Monstro'),
        (CHARACTER, 'Personagem'),
        (COMPANION, 'Companheiro'),
        (MAP_TOKEN, 'Miniatura de mapa'),
        (MAP_TILE, 'Tile de mapa'),
        (ITEM, 'Item'),
        (GENERIC, 'Generico'),
    )

    PUBLIC = 'public'
    OWNER = 'owner'
    VISIBILITY_CHOICES = (
        (PUBLIC, 'Publico'),
        (OWNER, 'Apenas dono'),
    )

    Name = models.CharField(max_length=120)
    Slug = models.SlugField(max_length=140, unique=True, blank=True)
    Category = models.CharField(max_length=24, choices=CATEGORY_CHOICES, default=GENERIC, db_index=True)
    OriginalImage = models.FileField(
        upload_to=sprite_upload_path,
        validators=[FileExtensionValidator(allowed_extensions=IMAGE_EXTENSIONS)],
        blank=True,
    )
    AltText = models.CharField(max_length=180, blank=True)
    Visibility = models.CharField(max_length=12, choices=VISIBILITY_CHOICES, default=PUBLIC, db_index=True)
    Owner = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    Width = models.PositiveIntegerField(default=0, blank=True)
    Height = models.PositiveIntegerField(default=0, blank=True)
    FileSize = models.PositiveIntegerField(default=0, blank=True)
    Checksum = models.CharField(max_length=64, blank=True, db_index=True)
    DefaultGridWidth = models.PositiveSmallIntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(64)])
    DefaultGridHeight = models.PositiveSmallIntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(64)])
    AnchorX = models.DecimalField(max_digits=4, decimal_places=3, default=0.5)
    AnchorY = models.DecimalField(max_digits=4, decimal_places=3, default=0.5)
    IsActive = models.BooleanField(default=True, db_index=True)
    CreatedAt = models.DateTimeField(auto_now_add=True)
    UpdatedAt = models.DateTimeField(auto_now=True)

    objects = SpriteAssetQuerySet.as_manager()

    class Meta:
        ordering = ('Category', 'Name')
        indexes = [
            models.Index(fields=('Category', 'IsActive')),
            models.Index(fields=('Visibility', 'IsActive')),
        ]

    def __str__(self):
        return self.Name

    @property
    def display_alt(self):
        return self.AltText or self.Name

    @property
    def original_url(self):
        return self.OriginalImage.url if self.OriginalImage else ''

    def save(self, *args, **kwargs):
        self.Name = (self.Name or '').strip()
        if not self.Slug:
            self.Slug = self._unique_slug()
        if self.OriginalImage:
            self.FileSize = getattr(self.OriginalImage, 'size', 0) or 0
            self.Checksum = file_checksum(self.OriginalImage)
        super().save(*args, **kwargs)

    def _unique_slug(self):
        base = slugify(self.Name)[:80] or 'sprite'
        slug = base
        suffix = 2
        qs = type(self).objects.all()
        if self.pk:
            qs = qs.exclude(pk=self.pk)
        while qs.filter(Slug=slug).exists():
            slug = f'{base}-{suffix}'
            suffix += 1
        return slug


class SpriteVariant(models.Model):
    THUMB_64 = 'thumb_64'
    ICON_96 = 'icon_96'
    TOKEN_128 = 'token_128'
    TOKEN_256 = 'token_256'
    PORTRAIT_320 = 'portrait_320'
    PORTRAIT_640 = 'portrait_640'

    VARIANT_CHOICES = (
        (THUMB_64, 'Thumb 64'),
        (ICON_96, 'Icone 96'),
        (TOKEN_128, 'Token 128'),
        (TOKEN_256, 'Token 256'),
        (PORTRAIT_320, 'Retrato 320'),
        (PORTRAIT_640, 'Retrato 640'),
    )

    SpriteAsset = models.ForeignKey(SpriteAsset, on_delete=models.CASCADE, related_name='variants')
    Variant = models.CharField(max_length=24, choices=VARIANT_CHOICES, db_index=True)
    File = models.FileField(
        upload_to=sprite_variant_upload_path,
        validators=[FileExtensionValidator(allowed_extensions=IMAGE_EXTENSIONS)],
        blank=True,
    )
    Width = models.PositiveIntegerField(default=0, blank=True)
    Height = models.PositiveIntegerField(default=0, blank=True)
    Format = models.CharField(max_length=16, blank=True)
    FileSize = models.PositiveIntegerField(default=0, blank=True)
    CreatedAt = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('SpriteAsset', 'Variant')
        constraints = [
            models.UniqueConstraint(fields=('SpriteAsset', 'Variant'), name='unique_sprite_variant_per_asset'),
        ]

    def __str__(self):
        return f'{self.SpriteAsset} - {self.Variant}'

    @property
    def url(self):
        return self.File.url if self.File else ''

    def save(self, *args, **kwargs):
        if self.File:
            self.FileSize = getattr(self.File, 'size', 0) or self.FileSize
        super().save(*args, **kwargs)


class SpriteBinding(models.Model):
    SDR_CLASS = 'sdr_class'
    SDR_MONSTER = 'sdr_monster'
    COMBATANT_KIND = 'combatant_kind'
    CHARACTER_CLASS = 'character_class'
    COMPANION_SPECIES = 'companion_species'

    TARGET_CHOICES = (
        (SDR_CLASS, 'Classe SDR'),
        (SDR_MONSTER, 'Monstro SDR'),
        (COMBATANT_KIND, 'Tipo de combatente'),
        (CHARACTER_CLASS, 'Classe da ficha'),
        (COMPANION_SPECIES, 'Especie de companheiro'),
    )

    CLASS_ICON = 'class_icon'
    CLASS_PORTRAIT = 'class_portrait'
    MONSTER_TOKEN = 'monster_token'
    MONSTER_PORTRAIT = 'monster_portrait'
    INITIATIVE_TOKEN = 'initiative_token'
    MAP_TOKEN = 'map_token'
    MAP_TILE = 'map_tile'

    PURPOSE_CHOICES = (
        (CLASS_ICON, 'Icone de classe'),
        (CLASS_PORTRAIT, 'Retrato de classe'),
        (MONSTER_TOKEN, 'Token de monstro'),
        (MONSTER_PORTRAIT, 'Retrato de monstro'),
        (INITIATIVE_TOKEN, 'Token de iniciativa'),
        (MAP_TOKEN, 'Token de mapa'),
        (MAP_TILE, 'Tile de mapa'),
    )

    TargetType = models.CharField(max_length=32, choices=TARGET_CHOICES, db_index=True)
    TargetKey = models.CharField(max_length=160, db_index=True)
    Purpose = models.CharField(max_length=32, choices=PURPOSE_CHOICES, db_index=True)
    SpriteAsset = models.ForeignKey(SpriteAsset, on_delete=models.CASCADE, related_name='bindings')
    CreatedAt = models.DateTimeField(auto_now_add=True)
    UpdatedAt = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('TargetType', 'TargetKey', 'Purpose')
        constraints = [
            models.UniqueConstraint(
                fields=('TargetType', 'TargetKey', 'Purpose'),
                name='unique_sprite_binding_target_purpose',
            ),
        ]
        indexes = [
            models.Index(fields=('TargetType', 'TargetKey', 'Purpose')),
        ]

    def __str__(self):
        return f'{self.TargetType}:{self.TargetKey} -> {self.SpriteAsset}'

    def save(self, *args, **kwargs):
        self.TargetKey = (self.TargetKey or '').strip()
        super().save(*args, **kwargs)
