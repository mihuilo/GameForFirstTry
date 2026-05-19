"""
WorldRenderer — рисует мир на экране.

Порядок работы:
  1. Для каждого видимого чанка
  2. Пересчитать dirty-клетки через AutoTiler
  3. Нарисовать каждую клетку: спрайт (autotile) или заливка (solid_color)

Рендер ничего не знает о логике мира — только о том, что и куда рисовать.
"""

import os
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

        # Кеш загруженных спрайтов: путь → pygame.Surface
        self._sprite_cache: dict[str, pygame.Surface] = {}

    def update_chunk_cache(self, chunk, neighbor_getter=None) -> None:
        """
        Пересчитывает bitmask для dirty-клеток чанка.

        neighbor_getter (опционально) — функция (world_x, world_y) → tile_id,
        позволяет учитывать соседей из других чанков.
        Если None — при выходе за границу чанка считаем "не соединяется".
        """
        dirty = chunk.get_dirty_cells()
        if not dirty:
            return

        grid = chunk.logical_grid

        for (lx, ly) in dirty:
            tile_id = grid[ly][lx]
            if not tile_id:
                continue

            # Строим временную мини-сетку вокруг клетки для compute_bitmask
            # Если neighbor_getter задан — подтягиваем соседей из других чанков
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

        # Перерисовываем поверхность чанка только если что-то изменилось
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

                pygame.draw.rect(target, (30, 100, 200), pygame.Rect(px, py, ts, ts))

                tile_id = chunk.logical_grid[y][x]
                bitmask = chunk.visual_cache[y][x]
                if tile_id != "dirt":
                    self._draw_tile(target, tile_id, bitmask, px, py)

        if hasattr(chunk, 'decoration'):
            for (lx, ly), deco_tile_id in chunk.decoration.items():
                dpx = lx * ts
                dpy = ly * ts
                bitmask = self._autotiler.compute_bitmask_deco(chunk, lx, ly, deco_getter)
                self._draw_tile(target, deco_tile_id, bitmask, dpx, dpy)

    def _draw_tile(self, surface, tile_id: str, bitmask: int, px: int, py: int):
        rect = pygame.Rect(px, py, self.tile_size, self.tile_size)

        sprite_path = self._autotiler.get_sprite_path(tile_id, bitmask)
        if sprite_path:
            sprite = self._load_sprite(sprite_path)
            if sprite:
                surface.blit(sprite, rect)  # ← убрали scale
                return

        color = self._autotiler.get_color(tile_id)
        if color:
            pygame.draw.rect(surface, color, rect)
            return

        pygame.draw.rect(surface, (255, 0, 255), rect)

    def _load_sprite(self, path) -> pygame.Surface | None:
        # path — либо str (отдельный файл), либо tuple (атлас, индекс)
        cache_key = path if isinstance(path, str) else f"{path[0]}:{path[1]}"

        if cache_key in self._sprite_cache:
            return self._sprite_cache[cache_key]

        if isinstance(path, tuple):
            atlas_path, index = path
            if not os.path.exists(atlas_path):
                self._sprite_cache[cache_key] = None
                return None
            try:
                sheet = pygame.image.load(atlas_path).convert_alpha()
                tile_w = sheet.get_width() // 4
                tile_h = sheet.get_height() // 4
                col = index % 4
                row = index // 4
                surface = pygame.Surface((tile_w, tile_h), pygame.SRCALPHA)
                surface.blit(sheet, (0, 0), pygame.Rect(col * tile_w, row * tile_h, tile_w, tile_h))
                # Масштабируем один раз здесь
                scaled = pygame.transform.scale(surface, (self.tile_size, self.tile_size))
                self._sprite_cache[cache_key] = scaled
                return scaled
            except Exception as e:
                print(f"[WorldRenderer] Не удалось загрузить атлас: {atlas_path} — {e}")
                self._sprite_cache[cache_key] = None
                return None

        if not os.path.exists(path):
            self._sprite_cache[cache_key] = None
            return None
        try:
            img = pygame.image.load(path).convert_alpha()
            # Масштабируем один раз здесь
            scaled = pygame.transform.scale(img, (self.tile_size, self.tile_size))
            self._sprite_cache[cache_key] = scaled
            return scaled
        except Exception as e:
            print(f"[WorldRenderer] Не удалось загрузить спрайт: {path} — {e}")
            self._sprite_cache[cache_key] = None
            return None

    def _build_expanded_grid(self, chunk, lx, ly, neighbor_getter) -> list[list[str]]:
        """
        Строит мини-сетку 3×3 вокруг клетки (lx, ly) с учётом соседних чанков.
        Центр = [1][1].
        """
        grid_3x3 = []
        for dy in range(-1, 2):
            row = []
            for dx in range(-1, 2):
                nx = chunk.chunk_x * chunk.size + lx + dx
                ny = chunk.chunk_y * chunk.size + ly + dy
                row.append(neighbor_getter(nx, ny) or "")
            grid_3x3.append(row)
        return grid_3x3
