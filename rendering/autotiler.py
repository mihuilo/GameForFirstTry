"""
AutoTiler — вычисляет bitmask и возвращает готовый Surface.
"""

import pygame
from world.tile_registry import TileRegistry
from world.tileset_registry import TilesetRegistry

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
        tile_id = grid[y][x]
        if not tile_id or not self._tiles.has(tile_id):
            return 0
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
                if grid[ny][nx] in connects_to:
                    bitmask |= bit
        return bitmask

    def compute_bitmask_8(self, grid: list[list[str]], x: int, y: int) -> int:
        tile_id = grid[y][x]
        if not tile_id or not self._tiles.has(tile_id):
            return 0
        tile_def = self._tiles.get(tile_id)
        tileset_id = tile_def.get("tileset", tile_id)

        try:
            connects_to = set(self._tilesets.get_connects_to(tileset_id))
        except KeyError:
            return 0

        height = len(grid)
        width = len(grid[0]) if height > 0 else 0

        def neighbor(dx, dy) -> bool:
            nx, ny = x + dx, y + dy
            if 0 <= nx < width and 0 <= ny < height:
                return grid[ny][nx] in connects_to
            return False

        n  = neighbor(0, -1)
        e  = neighbor(1,  0)
        s  = neighbor(0,  1)
        w  = neighbor(-1, 0)
        ne = neighbor(1, -1)
        se = neighbor(1,  1)
        sw = neighbor(-1, 1)
        nw = neighbor(-1,-1)

        bitmask = 0
        if n:              bitmask |= 1
        if e:              bitmask |= 2
        if s:              bitmask |= 4
        if w:              bitmask |= 8
        if n and e and ne: bitmask |= 16
        if s and e and se: bitmask |= 32
        if s and w and sw: bitmask |= 64
        if n and w and nw: bitmask |= 128
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
        if deco_getter(wx,     wy - 1) == tile_id: bitmask |= 1
        if deco_getter(wx + 1, wy    ) == tile_id: bitmask |= 2
        if deco_getter(wx,     wy + 1) == tile_id: bitmask |= 4
        if deco_getter(wx - 1, wy    ) == tile_id: bitmask |= 8
        return bitmask

    def get_surface(self, tile_id: str, bitmask: int, world_x: int = 0, world_y: int = 0) -> pygame.Surface | None:
        """Возвращает готовый Surface для тайла. None если не найден."""
        if not tile_id or not self._tiles.has(tile_id):
            return None
        tile_def = self._tiles.get(tile_id)
        tileset_id = tile_def.get("tileset", tile_id)
        try:
            return self._tilesets.get_surface(tileset_id, bitmask, world_x, world_y)
        except KeyError:
            return None

    def get_color(self, tile_id: str) -> tuple | None:
        if not tile_id or not self._tiles.has(tile_id):
            return None
        tile_def = self._tiles.get(tile_id)
        tileset_id = tile_def.get("tileset", tile_id)
        try:
            return self._tilesets.get_color(tileset_id)
        except (KeyError, TypeError):
            return None