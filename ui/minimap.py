"""
Minimap — миникарта в правом верхнем углу.
Показывает область вокруг игрока, чуть больше видимой зоны.
"""

import pygame


# Цвета тайлов на миникарте
TILE_COLORS = {
    "dirt":  (60, 180, 60),   # dirt визуально = трава
    "water": (30, 100, 200),
    "grass": (60, 180, 60),
    "":      (10, 10, 30),
}


class Minimap:
    def __init__(self, size: int = 200, tile_radius: int = 24):
        """
        size        — размер миникарты в пикселях
        tile_radius — сколько тайлов показывать в каждую сторону от игрока
        """
        self.size = size
        self.tile_radius = tile_radius
        self.visible = True
        self._surface = pygame.Surface((size, size))

    def toggle(self):
        self.visible = not self.visible

    def update(self, player_x: float, player_y: float, world_tile_size: int, get_tile_at):
        """Перерисовывает миникарту вокруг позиции игрока."""
        self._surface.fill((10, 10, 30))

        # Тайловые координаты игрока
        player_tx = int(player_x // world_tile_size)
        player_ty = int(player_y // world_tile_size)

        # Точка игрока по центру
        cx = self.size // 2
        cy = self.size // 2
        pygame.draw.circle(self._surface, (255, 255, 255), (cx, cy), 3)
        pygame.draw.circle(self._surface, (0, 0, 0), (cx, cy), 3, 1)

        diameter = self.tile_radius * 2 + 1
        tile_px = self.size / diameter  # размер одного тайла на миникарте

        for dy in range(-self.tile_radius, self.tile_radius + 1):
            for dx in range(-self.tile_radius, self.tile_radius + 1):
                tx = player_tx + dx
                ty = player_ty + dy

                tile_id = get_tile_at(tx, ty)
                color = TILE_COLORS.get(tile_id, (60, 180, 60))

                px = int((dx + self.tile_radius) * tile_px)
                py = int((dy + self.tile_radius) * tile_px)
                # +1 чтобы перекрывать зазоры
                size = max(1, int(tile_px) + 1)
                pygame.draw.rect(self._surface, color, (px, py, size, size))

        # Точка игрока по центру
        cx = self.size // 2
        cy = self.size // 2
        pygame.draw.circle(self._surface, (255, 255, 255), (cx, cy), 3)
        pygame.draw.circle(self._surface, (0, 0, 0), (cx, cy), 3, 1)

    def draw(self, surface: pygame.Surface):
        if not self.visible:
            return

        sw = surface.get_width()
        margin = 10

        # Рамка
        rect = pygame.Rect(sw - self.size - margin, margin, self.size, self.size)
        pygame.draw.rect(surface, (0, 0, 0), rect.inflate(4, 4), border_radius=6)
        surface.blit(self._surface, rect.topleft)
        pygame.draw.rect(surface, (100, 100, 100), rect, 2, border_radius=4)