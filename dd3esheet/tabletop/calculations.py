"""Pure tabletop calculations, without DB access."""

import math


def hex_dimensions(grid_size):
    """Return pointy-top hex dimensions for a flat-to-flat width."""
    size = float(grid_size)
    radius = size / math.sqrt(3)
    return {
        'radius': radius,
        'width': math.sqrt(3) * radius,
        'height': 2 * radius,
        'col_spacing': math.sqrt(3) * radius,
        'row_spacing': 1.5 * radius,
    }


def _cube_round(q, r):
    """Round fractional axial coordinates to the nearest hex."""
    x, z = q, r
    y = -x - z
    rx, ry, rz = round(x), round(y), round(z)
    dx, dy, dz = abs(rx - x), abs(ry - y), abs(rz - z)
    if dx > dy and dx > dz:
        rx = -ry - rz
    elif dy > dz:
        ry = -rx - rz
    else:
        rz = -rx - ry
    return rx, rz


def nearest_hex_center(x, y, grid_size):
    """Return the nearest pointy-top hex center in integer pixels."""
    radius = float(grid_size) / math.sqrt(3)
    q = (math.sqrt(3) / 3 * x - 1.0 / 3 * y) / radius
    r = (2.0 / 3 * y) / radius
    q, r = _cube_round(q, r)
    cx = math.sqrt(3) * radius * (q + r / 2)
    cy = 1.5 * radius * r
    return (round(cx), round(cy))


def axial_to_pixel(q, r, grid_size):
    """Return the pixel center for pointy-top axial coordinates."""
    radius = float(grid_size) / math.sqrt(3)
    x = math.sqrt(3) * radius * (q + r / 2)
    y = 1.5 * radius * r
    return (round(x), round(y))


def pixel_to_axial(x, y, grid_size):
    """Converte px de mundo para coordenada axial inteira (cube round)."""
    radius = float(grid_size) / math.sqrt(3)
    q = (math.sqrt(3) / 3 * x - 1.0 / 3 * y) / radius
    r = (2.0 / 3 * y) / radius
    return _cube_round(q, r)


def hex_distance(q1, r1, q2, r2):
    """Distância em hexes entre duas coordenadas axiais pointy-top."""
    dq = q1 - q2
    dr = r1 - r2
    return (abs(dq) + abs(dr) + abs(dq + dr)) // 2


def hex_disk(q, r, radius):
    """Todos os hexes axiais a distância <= radius do centro (q, r)."""
    cells = []
    for dq in range(-radius, radius + 1):
        lo = max(-radius, -dq - radius)
        hi = min(radius, -dq + radius)
        for dr in range(lo, hi + 1):
            cells.append((q + dq, r + dr))
    return cells


def _cube_lerp(a, b, t):
    return a + (b - a) * t


def hex_line(q1, r1, q2, r2):
    """Linha de hexes (inclusiva) de (q1,r1) a (q2,r2) via interpolação cúbica."""
    n = hex_distance(q1, r1, q2, r2)
    if n == 0:
        return [(q1, r1)]
    results = []
    for i in range(n + 1):
        t = i / n
        x = _cube_lerp(q1, q2, t)
        z = _cube_lerp(r1, r2, t)
        results.append(_cube_round(x, z))
    # dedup preservando ordem
    seen, out = set(), []
    for cell in results:
        if cell not in seen:
            seen.add(cell)
            out.append(cell)
    return out


def snap_to_grid(x, y, grid_size, grid_mode):
    """Snap coordinates to the nearest hex center in hex mode."""
    if grid_mode == 'hex' and grid_size and grid_size > 0:
        return nearest_hex_center(x, y, grid_size)
    return (int(x), int(y))


def point_in_rect(px, py, rx, ry, rw, rh):
    """True when point (px, py) is inside rectangle (rx, ry, rw, rh)."""
    return rx <= px <= rx + rw and ry <= py <= ry + rh


def token_hex_visible(q, r, fog_keys, is_owner):
    """Token (no hex q,r) visível? Dono vê tudo; jogador não vê hex em névoa."""
    if is_owner:
        return True
    return (q, r) not in fog_keys


def token_visible_to(token, fog_regions, is_owner):
    """Return whether a token should be rendered for the current viewer."""
    if is_owner:
        return True
    if getattr(token, 'Hidden', False):
        return False
    for fog in fog_regions:
        if point_in_rect(token.X, token.Y, fog.X, fog.Y, fog.Width, fog.Height):
            return False
    return True
