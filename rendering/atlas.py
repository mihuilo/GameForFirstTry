"""
Atlas — нарезает спрайт-атлас на отдельные тайлы по сетке.

Универсальный модуль, не зависит от игровой логики.
Работает с любым атласом: трава, анимации, UI, etc.

Использование:
    atlas = Atlas("assets/tiles/grass_atlas.png", tile_w=16, tile_h=16)
    surface = atlas.get(col=0, row=0)   # первый тайл
    surface = atlas.get_by_index(5)     # шестой тайл слева-направо сверху-вниз
"""

import pygame


class Atlas:
    def __init__(self, path: str, tile_w: int, tile_h: int):
        self._sheet = pygame.image.load(path).convert_alpha()
        self._tile_w = tile_w
        self._tile_h = tile_h
        self._cols = self._sheet.get_width() // tile_w
        self._rows = self._sheet.get_height() // tile_h
        self._cache: dict[tuple[int, int], pygame.Surface] = {}

        print(f"[Atlas] {path} → {self._cols}×{self._rows} тайлов ({tile_w}×{tile_h}px)")

    def get(self, col: int, row: int) -> pygame.Surface:
        """Вырезает тайл по колонке и строке (0-индексация)."""
        key = (col, row)
        if key in self._cache:
            return self._cache[key]

        surface = pygame.Surface((self._tile_w, self._tile_h), pygame.SRCALPHA)
        surface.blit(
            self._sheet,
            (0, 0),
            pygame.Rect(col * self._tile_w, row * self._tile_h, self._tile_w, self._tile_h)
        )
        self._cache[key] = surface
        return surface

    def get_by_index(self, index: int) -> pygame.Surface:
        """Вырезает тайл по порядковому номеру (слева-направо, сверху-вниз)."""
        col = index % self._cols
        row = index // self._cols
        return self.get(col, row)

    @property
    def cols(self) -> int:
        return self._cols

    @property
    def rows(self) -> int:
        return self._rows

    @property
    def tile_size(self) -> tuple[int, int]:
        return self._tile_w, self._tile_h