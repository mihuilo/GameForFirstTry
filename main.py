"""
main.py — точка входа. Запуск: python main.py
"""

import pygame
import sys
import os
from world.generators.decoration_gen import DecorationGenerator

sys.path.insert(0, os.path.dirname(__file__))

from world.tile_registry import TileRegistry
from world.tileset_registry import TilesetRegistry
from world.chunk import Chunk
from world.generators.terrain_gen import TerrainGenerator
from rendering.autotiler import AutoTiler
from rendering.world_renderer import WorldRenderer
from entities.player import Player
from ui.menu import PauseMenu
from ui.minimap import Minimap
from world.object_registry import ObjectRegistry
from world.generators.object_gen import ObjectGenerator
from rendering.object_renderer import ObjectRenderer

BASE_DIR     = os.path.dirname(__file__)
DATA_TILES   = os.path.join(BASE_DIR, "data/tiles")
DATA_TSETS   = os.path.join(BASE_DIR, "data/tilesets")
DATA_BIOMES  = os.path.join(BASE_DIR, "data/biomes")
DATA_GEN     = os.path.join(BASE_DIR, "data/generation/world.json")
ASSETS_TILES = os.path.join(BASE_DIR, "assets/tiles")
ASSETS_PLAYER = os.path.join(BASE_DIR, "assets/player")

TILE_SIZE   = 32
SCREEN_W    = 1280
SCREEN_H    = 720
CHUNKS_VIEW = 3

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H), pygame.RESIZABLE)
    pygame.display.set_caption("IndieGame")
    clock = pygame.time.Clock()

    tile_reg = TileRegistry(DATA_TILES)
    tileset_reg = TilesetRegistry(DATA_TSETS, ASSETS_TILES, tile_size=TILE_SIZE)
    autotiler = AutoTiler(tile_reg, tileset_reg)
    renderer = WorldRenderer(tile_reg, tileset_reg, autotiler, tile_size=TILE_SIZE)
    terrain_gen = TerrainGenerator(DATA_GEN, DATA_BIOMES)
    obj_registry = ObjectRegistry("data/objects", tile_size=TILE_SIZE)
    obj_gen = ObjectGenerator(obj_registry, seed=42)
    obj_renderer = ObjectRenderer(obj_registry, tile_size=TILE_SIZE)

    chunks: dict[tuple[int,int], Chunk] = {}
    chunk_size = 16

    for cy in range(-CHUNKS_VIEW, CHUNKS_VIEW + 1):
        for cx in range(-CHUNKS_VIEW, CHUNKS_VIEW + 1):
            chunk = Chunk(cx, cy, chunk_size)
            terrain_gen.fill_chunk(chunk)
            chunks[(cx, cy)] = chunk

    def get_tile_at(wx: int, wy: int) -> str:
        if wx < 0:
            cx = -((-wx - 1) // chunk_size) - 1
            lx = chunk_size - 1 - ((-wx - 1) % chunk_size)
        else:
            cx = wx // chunk_size
            lx = wx % chunk_size

        if wy < 0:
            cy = -((-wy - 1) // chunk_size) - 1
            ly = chunk_size - 1 - ((-wy - 1) % chunk_size)
        else:
            cy = wy // chunk_size
            ly = wy % chunk_size

        c = chunks.get((cx, cy))
        if c:
            return c.get_tile(lx, ly)
        return "water"  # за границей загруженных чанков — вода, не пройти

    for chunk in chunks.values():
        renderer.update_chunk_cache(chunk, neighbor_getter=get_tile_at)

    deco_gen = DecorationGenerator(DATA_TILES)
    for chunk in chunks.values():
        chunk.decoration = deco_gen.fill_chunk(chunk, get_tile_at)

    obj_registry = ObjectRegistry("data/objects", tile_size=TILE_SIZE)
    obj_gen = ObjectGenerator(obj_registry, seed=42)

    for chunk in chunks.values():
        chunk.objects = obj_gen.fill_chunk(chunk, get_tile_at)

    deco_map: dict[tuple[int, int], str] = {}
    for chunk in chunks.values():
        for (lx, ly), tile_id in chunk.decoration.items():
            wx = chunk.chunk_x * chunk_size + lx
            wy = chunk.chunk_y * chunk_size + ly
            deco_map[(wx, wy)] = tile_id

    def get_object_at(wx: int, wy: int) -> str:
        cx = wx // chunk_size
        cy = wy // chunk_size
        lx = wx % chunk_size
        ly = wy % chunk_size
        c = chunks.get((cx, cy))
        if c and hasattr(c, 'objects'):
            return c.objects.get((lx, ly), "")
        return ""

    def get_deco_at(wx: int, wy: int) -> str:
        return deco_map.get((wx, wy), "")

    # --- Персонаж ---
    player = Player(ASSETS_PLAYER, TILE_SIZE*5, tile_reg, world_tile_size=TILE_SIZE, obj_registry=obj_registry)
    player.x = 0.0
    player.y = 0.0

    cam_x = 0.0
    cam_y = 0.0

    font = pygame.font.SysFont("monospace", 14)

    menu = PauseMenu()
    minimap = Minimap(size=200, tile_radius=24)
    zoom = menu.zoom

    running = True
    while running:
        dt = clock.tick(320) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                menu.toggle()
                continue  # не передаём ESC дальше в handle_event

            if event.type == pygame.KEYDOWN and event.key == pygame.K_m:
                minimap.toggle()

            should_quit = menu.handle_event(event)
            if should_quit:
                running = False

        keys = pygame.key.get_pressed()
        player.update(dt, keys, get_tile_at, get_object_at)

        # Камера следует за персонажем
        cam_x, cam_y = player.get_camera_target(int(screen.get_width() / zoom), int(screen.get_height() / zoom))

        zoom = menu.zoom
        screen.fill((51, 157, 181))

        world_w = int(screen.get_width() / zoom)
        world_h = int(screen.get_height() / zoom)
        world_surface = pygame.Surface((world_w, world_h))
        world_surface.fill((51, 157, 181))

        for chunk in chunks.values():
            chunk_px = chunk.chunk_x * chunk_size * TILE_SIZE - int(cam_x)
            chunk_py = chunk.chunk_y * chunk_size * TILE_SIZE - int(cam_y)
            chunk_size_px = chunk_size * TILE_SIZE

            # Увеличиваем отступ для объектов которые выступают за границы чанка
            obj_margin = TILE_SIZE * 12

            if chunk_px + chunk_size_px < -obj_margin or chunk_px > world_w + obj_margin:
                continue
            if chunk_py + chunk_size_px < -obj_margin or chunk_py > world_h + obj_margin:
                continue
            renderer.render_chunk(world_surface, chunk, int(cam_x), int(cam_y), deco_getter=get_deco_at)

        obj_renderer.render_sorted(world_surface, chunks, int(cam_x), int(cam_y), chunk_size, player, cam_x, cam_y)

        scaled = pygame.transform.scale(world_surface, (screen.get_width(), screen.get_height()))
        screen.blit(scaled, (0, 0))

        menu.draw(screen)
        minimap.update(player.x, player.y, TILE_SIZE, get_tile_at)
        minimap.draw(screen)

        if menu.show_fps:
            fps = clock.get_fps()
            fps_txt = font.render(f"FPS: {fps:.0f}", True, (200, 200, 200))
            screen.blit(fps_txt, (8, 8))

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()