"""
WorldRenderer — рисует мир на экране.
"""

import pygame

from rendering.autotiler import AutoTiler
from world.tile_registry import TileRegistry
from world.tileset_registry import TilesetRegistry


class WorldRenderer:
    def __init__(
        self,
        tile_registry: TileRegistry,
        tileset_registry: TilesetRegistry,
        autotiler: AutoTiler,
        tile_size: int = 32,
    ):
        self._tiles = tile_registry
        self._tilesets = tileset_registry
        self._autotiler = autotiler
        self.tile_size = tile_size

    def update_chunk_cache(self, chunk, neighbor_getter=None) -> None:
        dirty = chunk.get_dirty_cells()
        if not dirty:
            return

        grid = chunk.logical_grid

        for (lx, ly) in dirty:
            tile_id = grid[ly][lx]
            if not tile_id:
                continue

            ts_type = ""
            if self._tiles.has(tile_id):
                tileset_id = self._tiles.get(tile_id).get("tileset", tile_id)
                try:
                    ts_type = self._tilesets.get_type(tileset_id)
                except:
                    pass

            if ts_type == "8bit_autotile":
                if neighbor_getter:
                    expanded = self._build_expanded_grid(chunk, lx, ly, neighbor_getter)
                    bitmask = self._autotiler.compute_bitmask_8(expanded, 1, 1)
                else:
                    bitmask = self._autotiler.compute_bitmask_8(grid, lx, ly)
            else:
                if neighbor_getter:
                    expanded = self._build_expanded_grid(chunk, lx, ly, neighbor_getter)
                    bitmask = self._autotiler.compute_bitmask(expanded, 1, 1)
                else:
                    bitmask = self._autotiler.compute_bitmask(grid, lx, ly)

            chunk.set_bitmask(lx, ly, bitmask)

    def render_chunk(self, surface: pygame.Surface, chunk, camera_x: int, camera_y: int, deco_getter=None) -> None:
        ts = self.tile_size
        chunk_pixel_x = chunk.chunk_x * chunk.size * ts - camera_x
        chunk_pixel_y = chunk.chunk_y * chunk.size * ts - camera_y
        chunk_size_px = chunk.size * ts

        if chunk.surface_dirty or chunk.cached_surface is None:
            chunk.cached_surface = pygame.Surface((chunk_size_px, chunk_size_px), pygame.SRCALPHA)
            self._render_chunk_to_surface(chunk.cached_surface, chunk, deco_getter)
            chunk.surface_dirty = False

        surface.blit(chunk.cached_surface, (chunk_pixel_x, chunk_pixel_y))

    def _render_chunk_to_surface(self, target, chunk, deco_getter=None):
        ts = self.tile_size

        for y in range(chunk.size):
            for x in range(chunk.size):
                px = x * ts
                py = y * ts
                wx = chunk.chunk_x * chunk.size + x
                wy = chunk.chunk_y * chunk.size + y

                pygame.draw.rect(target, (51, 157, 181), pygame.Rect(px, py, ts, ts))

                tile_id = chunk.logical_grid[y][x]
                bitmask = chunk.visual_cache[y][x]
                if tile_id != "dirt":
                    self._draw_tile(target, tile_id, bitmask, px, py, wx, wy)

        if hasattr(chunk, 'decoration'):
            for (lx, ly), deco_tile_id in chunk.decoration.items():
                dpx = lx * ts
                dpy = ly * ts
                wx = chunk.chunk_x * chunk.size + lx
                wy = chunk.chunk_y * chunk.size + ly
                bitmask = self._autotiler.compute_bitmask_deco(chunk, lx, ly, deco_getter)
                self._draw_tile(target, deco_tile_id, bitmask, dpx, dpy, wx, wy)

    def _draw_tile(self, surface, tile_id: str, bitmask: int, px: int, py: int, wx: int = 0, wy: int = 0):
        rect = pygame.Rect(px, py, self.tile_size, self.tile_size)

        # Спрайт через autotiler — он сам знает про атласы и форматы
        sprite = self._autotiler.get_surface(tile_id, bitmask, wx, wy)
        if sprite:
            surface.blit(sprite, rect)
            return

        # Solid color fallback
        color = self._autotiler.get_color(tile_id)
        if color:
            pygame.draw.rect(surface, color, rect)
            return

        # Не найден — фуксия
        print(f"[DEBUG] tile={tile_id} bitmask={bitmask} — не найден спрайт")
        pygame.draw.rect(surface, (255, 0, 255), rect)

    def _build_expanded_grid(self, chunk, lx, ly, neighbor_getter) -> list[list[str]]:
        grid_3x3 = []
        for dy in range(-1, 2):
            row = []
            for dx in range(-1, 2):
                nx = chunk.chunk_x * chunk.size + lx + dx
                ny = chunk.chunk_y * chunk.size + ly + dy
                row.append(neighbor_getter(nx, ny) or "")
            grid_3x3.append(row)
        return grid_3x3