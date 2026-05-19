"""
AutoTiler — вычисляет визуальный тайл (спрайт) для каждой клетки
на основе 4-битной маски соседей.

Биты маски:
    N = 1  (сосед сверху)
    E = 2  (сосед справа)
    S = 4  (сосед снизу)
    W = 8  (сосед слева)

Логика "сосед считается" — если он принадлежит к connects_to тайлсета.
Например, dirt connects_to=["dirt"], значит только dirt-сосед даёт бит.

Использование:
    autotiler = AutoTiler(tile_registry, tileset_registry)
    bitmask = autotiler.compute_bitmask(grid, x, y)
    sprite  = autotiler.get_sprite(tile_id, bitmask)
"""

from world.tile_registry import TileRegistry
from world.tileset_registry import TilesetRegistry

# Порядок соседей: (dx, dy, bit)
# (0, -1) = север, (1, 0) = восток, (0, 1) = юг, (-1, 0) = запад
_NEIGHBORS = [
    (0, -1, 1),   # N
    (1,  0, 2),   # E
    (0,  1, 4),   # S
    (-1, 0, 8),   # W
]


class AutoTiler:
    def __init__(self, tile_registry: TileRegistry, tileset_registry: TilesetRegistry):
        self._tiles = tile_registry
        self._tilesets = tileset_registry

    def compute_bitmask(self, grid: list[list[str]], x: int, y: int) -> int:
        """
        grid — двумерный список tile_id (строки = y, колонки = x).
        Возвращает bitmask 0–15.
        """
        tile_id = grid[y][x]
        tile_def = self._tiles.get(tile_id)
        tileset_id = tile_def.get("tileset", tile_id)

        try:
            connects_to = set(self._tilesets.get_connects_to(tileset_id))
        except KeyError:
            return 0

        height = len(grid)
        width = len(grid[0]) if height > 0 else 0

        bitmask = 0
        for dx, dy, bit in _NEIGHBORS:
            nx, ny = x + dx, y + dy
            if 0 <= nx < width and 0 <= ny < height:
                neighbor_id = grid[ny][nx]
                if neighbor_id in connects_to:
                    bitmask |= bit
            # Если сосед за границей карты — считаем как "не соединяется"
            # Можно изменить на "соединяется" если нужно зеркалирование краёв

        return bitmask

    def compute_bitmask_deco(self, chunk, lx, ly, deco_getter) -> int:
        if deco_getter is None:
            return 0
        tile_id = chunk.decoration.get((lx, ly), "")
        if not tile_id:
            return 0
        bitmask = 0
        wx = chunk.chunk_x * chunk.size + lx
        wy = chunk.chunk_y * chunk.size + ly
        if deco_getter(wx, wy - 1) == tile_id: bitmask |= 1  # N
        if deco_getter(wx + 1, wy) == tile_id: bitmask |= 2  # E
        if deco_getter(wx, wy + 1) == tile_id: bitmask |= 4  # S
        if deco_getter(wx - 1, wy) == tile_id: bitmask |= 8  # W
        return bitmask

    def get_sprite_path(self, tile_id: str, bitmask: int) -> str | None:
        """
        Возвращает путь к спрайту или None если тайл не autotile.
        """
        tile_def = self._tiles.get(tile_id)
        tileset_id = tile_def.get("tileset", tile_id)

        try:
            ts_type = self._tilesets.get_type(tileset_id)
        except KeyError:
            return None

        if ts_type == "4bit_autotile":
            return self._tilesets.get_sprite_path(tileset_id, bitmask)

        return None

    def get_color(self, tile_id: str) -> tuple | None:
        """
        Для solid_color тайлов возвращает (R, G, B), иначе None.
        """
        tile_def = self._tiles.get(tile_id)
        tileset_id = tile_def.get("tileset", tile_id)

        try:
            ts_type = self._tilesets.get_type(tileset_id)
        except KeyError:
            return None

        if ts_type == "solid_color":
            return self._tilesets.get_color(tileset_id)

        return None
