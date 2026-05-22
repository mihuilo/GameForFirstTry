"""
ObjectRenderer — рисует слой объектов поверх мира.
Объекты рисуются каждый кадр отдельно (не кешируются в chunk surface)
потому что у них будут анимации и состояния.
"""

import pygame
from world.object_registry import ObjectRegistry


class ObjectRenderer:
    def __init__(self, object_registry: ObjectRegistry, tile_size: int = 32):
        self._registry = object_registry
        self._tile_size = tile_size

    def render(self, surface: pygame.Surface, chunks: dict,
               camera_x: int, camera_y: int, chunk_size: int):
        ts = self._tile_size

        for chunk in chunks.values():
            if not hasattr(chunk, 'objects') or not chunk.objects:
                continue

            chunk_pixel_x = chunk.chunk_x * chunk_size * ts - camera_x
            chunk_pixel_y = chunk.chunk_y * chunk_size * ts - camera_y

            # Сортируем по Y чтобы объекты ниже рисовались поверх
            sorted_objects = sorted(chunk.objects.items(), key=lambda item: item[0][1])

            for (lx, ly), obj_id in sorted_objects:
                px = chunk_pixel_x + lx * ts
                py = chunk_pixel_y + ly * ts

                # Culling
                if px + ts * 3 < 0 or px > surface.get_width():
                    continue
                if py + ts * 3 < 0 or py > surface.get_height():
                    continue

                self._draw_object(surface, obj_id, px, py)

    def render_sorted(self, surface, chunks, camera_x, camera_y, chunk_size, player, cam_x, cam_y):
        ts = self._tile_size
        draw_list = []

        for chunk in chunks.values():
            if not hasattr(chunk, 'objects') or not chunk.objects:
                continue
            chunk_pixel_x = chunk.chunk_x * chunk_size * ts - camera_x
            chunk_pixel_y = chunk.chunk_y * chunk_size * ts - camera_y

            for (lx, ly), obj_id in chunk.objects.items():
                px = chunk_pixel_x + lx * ts
                py = chunk_pixel_y + ly * ts

                world_y = (chunk.chunk_y * chunk_size + ly + 1) * ts
                draw_list.append((world_y, lambda s, o=obj_id, x=px, y=py: self._draw_object(s, o, x, y)))

        player_world_y = player.y + player.tile_size * 0.8
        draw_list.append((player_world_y, lambda s, px=cam_x, py=cam_y: player.draw(s, px, py)))

        draw_list.sort(key=lambda item: item[0])
        for _, draw_fn in draw_list:
            draw_fn(surface)

    def _draw_object(self, surface, obj_id: str, px: int, py: int):
        if not self._registry.has(obj_id):
            return

        obj_def = self._registry.get(obj_id)
        sprite = self._registry.get_surface(obj_id)

        if not sprite:
            pygame.draw.rect(surface, (255, 0, 255),
                             pygame.Rect(px, py, self._tile_size, self._tile_size))
            return

        orig_w = obj_def["tile_w"]
        orig_h = obj_def["tile_h"]
        scale_factor = obj_def.get("scale", 1.0)
        scale = self._tile_size / orig_w * scale_factor
        dst_w = int(orig_w * scale)
        dst_h = int(orig_h * scale)

        real_x = px - dst_w // 2 + self._tile_size // 2
        draw_y = py - dst_h + self._tile_size

        if real_x + dst_w < 0 or real_x > surface.get_width():
            return
        if draw_y + dst_h < 0 or draw_y > surface.get_height():
            return

        scaled = pygame.transform.scale(sprite, (dst_w, dst_h))
        surface.blit(scaled, (real_x, draw_y))

        scaled = pygame.transform.scale(sprite, (dst_w, dst_h))
        surface.blit(scaled, (px - dst_w // 2 + self._tile_size // 2, draw_y))