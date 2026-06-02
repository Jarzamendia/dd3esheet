from typing import Optional
from .models import SDR_Spell


def resolve_spell(name: Optional[str]) -> Optional[SDR_Spell]:
    """Resolve um nome de magia para o registro SDR_Spell correspondente.

    Busca primeiro por `name__iexact`, depois por `altname__iexact`.
    Em caso de empate, retorna a primeira por `id`.
    Retorna `None` para string vazia, None ou nome desconhecido.
    """
    if not name or not name.strip():
        return None
    cleaned = name.strip()
    qs = SDR_Spell.objects.using('sdr')
    match = qs.filter(name__iexact=cleaned).order_by('id').first()
    if match is not None:
        return match
    return qs.filter(altname__iexact=cleaned).order_by('id').first()
