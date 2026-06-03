from django.contrib import admin

from .models import SpriteAsset, SpriteBinding, SpriteVariant
from .services import generate_missing_variants


class SpriteVariantInline(admin.TabularInline):
    model = SpriteVariant
    extra = 0
    fields = ('Variant', 'File', 'Width', 'Height', 'Format', 'FileSize')
    readonly_fields = ('FileSize',)


@admin.action(description='Gerar variantes ausentes')
def generate_variants(modeladmin, request, queryset):
    for asset in queryset:
        generate_missing_variants(asset)


@admin.register(SpriteAsset)
class SpriteAssetAdmin(admin.ModelAdmin):
    list_display = ('Name', 'Category', 'Visibility', 'IsActive', 'UpdatedAt')
    list_filter = ('Category', 'Visibility', 'IsActive')
    search_fields = ('Name', 'AltText', 'Slug')
    readonly_fields = ('Slug', 'FileSize', 'Checksum', 'CreatedAt', 'UpdatedAt')
    inlines = (SpriteVariantInline,)
    actions = (generate_variants,)


@admin.register(SpriteBinding)
class SpriteBindingAdmin(admin.ModelAdmin):
    list_display = ('TargetType', 'TargetKey', 'Purpose', 'SpriteAsset')
    list_filter = ('TargetType', 'Purpose')
    search_fields = ('TargetKey', 'SpriteAsset__Name')


@admin.register(SpriteVariant)
class SpriteVariantAdmin(admin.ModelAdmin):
    list_display = ('SpriteAsset', 'Variant', 'Width', 'Height', 'Format', 'FileSize')
    list_filter = ('Variant', 'Format')
    search_fields = ('SpriteAsset__Name',)
