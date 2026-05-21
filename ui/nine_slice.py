"""
NineSlice — рендерит панель из 9-slice спрайта.
"""

import pygame


class NineSlice:
    SLICE = 18

    def __init__(self, path: str, scale: int = 2):
        self._sheet = pygame.image.load(path).convert_alpha()
        self._scale = scale

    def draw(self, surface: pygame.Surface, rect: pygame.Rect):
        s_src = self.SLICE  # размер куска в атласе (18px)
        s_dst = self.SLICE * self._scale  # размер куска на экране
        x, y, w, h = rect.x, rect.y, rect.width, rect.height

        pieces = [
            # Углы
            (0, 0, x, y, s_dst, s_dst),
            (2, 0, x + w - s_dst, y, s_dst, s_dst),
            (0, 2, x, y + h - s_dst, s_dst, s_dst),
            (2, 2, x + w - s_dst, y + h - s_dst, s_dst, s_dst),
            # Края
            (1, 0, x + s_dst, y, w - s_dst * 2, s_dst),
            (1, 2, x + s_dst, y + h - s_dst, w - s_dst * 2, s_dst),
            (0, 1, x, y + s_dst, s_dst, h - s_dst * 2),
            (2, 1, x + w - s_dst, y + s_dst, s_dst, h - s_dst * 2),
            # Центр
            (1, 1, x + s_dst, y + s_dst, w - s_dst * 2, h - s_dst * 2),
        ]

        for src_col, src_row, dx, dy, dw, dh in pieces:
            # Вырезаем по оригинальному размеру
            src = pygame.Rect(src_col * s_src, src_row * s_src, s_src, s_src)
            tile = pygame.Surface((s_src, s_src), pygame.SRCALPHA)
            tile.blit(self._sheet, (0, 0), src)
            scaled = pygame.transform.scale(tile, (dw, dh))
            surface.blit(scaled, (dx, dy))