"""
main.py — точка входа. Запуск: python main.py

Этап 1: генерация одного чанка, autotile, отрисовка.
"""

import pygame
import sys
import os
from world.generators.decoration_gen import DecorationGenerator

# Добавляем корень проекта в путь
sys.path.insert(0, os.path.dirname(__file__))

from world.tile_registry import TileRegistry
from world.tileset_registry import TilesetRegistry
from world.chunk import Chunk
from world.generators.terrain_gen import TerrainGenerator
from rendering.autotiler import AutoTiler
from rendering.world_renderer import WorldRenderer

# --- Пути ---
BASE_DIR    = os.path.dirname(__file__)
DATA_TILES  = os.path.join(BASE_DIR, "data/tiles")
DATA_TSETS  = os.path.join(BASE_DIR, "data/tilesets")
DATA_BIOMES = os.path.join(BASE_DIR, "data/biomes")
DATA_GEN    = os.path.join(BASE_DIR, "data/generation/world.json")
ASSETS_TILES = os.path.join(BASE_DIR, "assets/tiles")

TILE_SIZE   = 32
SCREEN_W    = 1280
SCREEN_H    = 720
CHUNKS_VIEW = 3   # сколько чанков в каждую сторону от центра грузить

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H), pygame.RESIZABLE)
    pygame.display.set_caption("IndieGame — Этап 1: Autotile")
    clock = pygame.time.Clock()

    # --- Инициализация систем ---
    tile_reg    = TileRegistry(DATA_TILES)
    tileset_reg = TilesetRegistry(DATA_TSETS, ASSETS_TILES)
    autotiler   = AutoTiler(tile_reg, tileset_reg)
    renderer    = WorldRenderer(tile_reg, tileset_reg, autotiler, tile_size=TILE_SIZE)
    terrain_gen = TerrainGenerator(DATA_GEN, DATA_BIOMES)

    # --- Генерируем несколько чанков ---
    chunks: dict[tuple[int,int], Chunk] = {}
    chunk_size = 16

    for cy in range(-CHUNKS_VIEW, CHUNKS_VIEW + 1):
        for cx in range(-CHUNKS_VIEW, CHUNKS_VIEW + 1):
            chunk = Chunk(cx, cy, chunk_size)
            terrain_gen.fill_chunk(chunk)
            chunks[(cx, cy)] = chunk

    def get_tile_at(wx: int, wy: int) -> str:
        """Получить tile_id по мировым координатам (для межчанковых соседей)."""
        cx = wx // chunk_size
        cy = wy // chunk_size
        lx = wx % chunk_size
        ly = wy % chunk_size
        c = chunks.get((cx, cy))
        if c:
            return c.get_tile(lx, ly)
        return ""

    # Пересчитываем visual_cache для всех чанков с учётом соседей
    for chunk in chunks.values():
        renderer.update_chunk_cache(chunk, neighbor_getter=get_tile_at)
    deco_gen = DecorationGenerator(DATA_TILES)
    for chunk in chunks.values():
        chunk.decoration = deco_gen.fill_chunk(chunk, get_tile_at)

    deco_map: dict[tuple[int, int], str] = {}
    for chunk in chunks.values():
        for (lx, ly), tile_id in chunk.decoration.items():
            wx = chunk.chunk_x * chunk_size + lx
            wy = chunk.chunk_y * chunk_size + ly
            deco_map[(wx, wy)] = tile_id

    def get_deco_at(wx: int, wy: int) -> str:
        return deco_map.get((wx, wy), "")

    # --- Камера ---
    cam_x = -SCREEN_W // 2
    cam_y = -SCREEN_H // 2
    cam_speed = 300  # пикселей/сек

    font = pygame.font.SysFont("monospace", 14)

    running = True
    while running:
        dt = clock.tick(320) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

        # Движение камеры
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]  or keys[pygame.K_a]: cam_x -= cam_speed * dt
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: cam_x += cam_speed * dt
        if keys[pygame.K_UP]    or keys[pygame.K_w]: cam_y -= cam_speed * dt
        if keys[pygame.K_DOWN]  or keys[pygame.K_s]: cam_y += cam_speed * dt

        # --- Отрисовка ---
        screen.fill((10, 10, 30))  # фон = тёмно-синий (там где нет чанков)

        for chunk in chunks.values():
            chunk_px = chunk.chunk_x * chunk_size * TILE_SIZE - int(cam_x)
            chunk_py = chunk.chunk_y * chunk_size * TILE_SIZE - int(cam_y)
            chunk_size_px = chunk_size * TILE_SIZE

            if chunk_px + chunk_size_px < 0 or chunk_px > screen.get_width():
                continue
            if chunk_py + chunk_size_px < 0 or chunk_py > screen.get_height():
                continue

            renderer.render_chunk(screen, chunk, int(cam_x), int(cam_y), deco_getter=get_deco_at)

        # HUD
        fps = clock.get_fps()
        cam_tile_x = int(cam_x // TILE_SIZE)
        cam_tile_y = int(cam_y // TILE_SIZE)
        hud = font.render(
            f"FPS: {fps:.0f}  Камера: ({cam_tile_x}, {cam_tile_y})  "
            f"WASD/стрелки — движение  ESC — выход",
            True, (200, 200, 200)
        )
        screen.blit(hud, (8, 8))
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
