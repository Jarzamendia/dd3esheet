"""Funções puras da mesa virtual — sem DB, testáveis com `SimpleTestCase`."""


def snap_to_grid(x, y, grid_size, grid_mode):
    """Encaixa o centro (x, y) no centro da célula da grade em modo 'square'.

    Em modo 'free' (ou com `grid_size` inválido) devolve as coordenadas
    inalteradas. Coordenadas são o centro do token em px do mapa.
    """
    if grid_mode != 'square' or not grid_size or grid_size <= 0:
        return (int(x), int(y))
    cell = int(grid_size)
    cx = (int(x) // cell) * cell + cell // 2
    cy = (int(y) // cell) * cell + cell // 2
    return (cx, cy)


def point_in_rect(px, py, rx, ry, rw, rh):
    """True se o ponto (px, py) está dentro do retângulo (rx, ry, rw, rh)."""
    return rx <= px <= rx + rw and ry <= py <= ry + rh


def token_visible_to(token, fog_regions, is_owner):
    """Define se um token deve ser renderizado para quem está olhando.

    O dono vê tudo. Para não-donos, oculta tokens marcados como `Hidden` e
    tokens cujo centro cai dentro de qualquer região de névoa. Isso é aplicado
    no servidor para não vazar a posição de inimigos no HTML do jogador.
    """
    if is_owner:
        return True
    if getattr(token, 'Hidden', False):
        return False
    for fog in fog_regions:
        if point_in_rect(token.X, token.Y, fog.X, fog.Y, fog.Width, fog.Height):
            return False
    return True
