"""
Slider — ползунок с кастомным спрайтом.
Вертикальный и горизонтальный варианты.
"""

import pygame


class Slider:
    def __init__(self, handle_path: str, scale: int = 3,
                 min_val: int = 0, max_val: int = 100,
                 orientation: str = "horizontal"):
        self._sheet = pygame.image.load(handle_path).convert_alpha()
        self._scale = scale
        self._min = min_val
        self._max = max_val
        self._orientation = orientation  # "horizontal" или "vertical"
        self._dragging = False
        self._value = min_val

        # Размер спрайта ручки
        if orientation == "horizontal":
            self._handle_w = 16
            self._handle_h = 8
        else:
            self._handle_w = 8
            self._handle_h = 16

    @property
    def value(self) -> int:
        return self._value

    @value.setter
    def value(self, v: int):
        self._value = max(self._min, min(self._max, v))

    def handle_event(self, event, track_rect: pygame.Rect) -> bool:
        """Возвращает True если значение изменилось."""
        handle_rect = self._get_handle_rect(track_rect)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if handle_rect.collidepoint(event.pos) or track_rect.collidepoint(event.pos):
                self._dragging = True
                self._update_from_mouse(event.pos, track_rect)
                return True

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self._dragging = False

        if event.type == pygame.MOUSEMOTION and self._dragging:
            self._update_from_mouse(event.pos, track_rect)
            return True

        return False

    def _update_from_mouse(self, pos, track_rect: pygame.Rect):
        if self._orientation == "horizontal":
            rel = (pos[0] - track_rect.x) / track_rect.width
        else:
            rel = (pos[1] - track_rect.y) / track_rect.height
        rel = max(0.0, min(1.0, rel))
        self._value = round(self._min + rel * (self._max - self._min))

    def draw(self, surface: pygame.Surface, track_rect: pygame.Rect,
             track_color: tuple = (160, 100, 50),
             filled_color: tuple = (200, 140, 70)):
        # Трек
        pygame.draw.rect(surface, track_color, track_rect, border_radius=4)

        # Заполненная часть
        progress = (self._value - self._min) / (self._max - self._min)
        if self._orientation == "horizontal":
            filled = pygame.Rect(track_rect.x, track_rect.y,
                                 int(track_rect.w * progress), track_rect.h)
        else:
            filled_h = int(track_rect.h * progress)
            filled = pygame.Rect(track_rect.x, track_rect.y,
                                 track_rect.w, filled_h)
        pygame.draw.rect(surface, filled_color, filled, border_radius=4)

        # Ручка
        handle_rect = self._get_handle_rect(track_rect)
        hw = self._handle_w * self._scale
        hh = self._handle_h * self._scale
        handle_surf = pygame.transform.scale(self._sheet, (hw, hh))
        surface.blit(handle_surf, handle_rect.topleft)

    def _get_handle_rect(self, track_rect: pygame.Rect) -> pygame.Rect:
        hw = self._handle_w * self._scale
        hh = self._handle_h * self._scale
        progress = (self._value - self._min) / (self._max - self._min)

        if self._orientation == "horizontal":
            # Ручка накладывается на правую границу трека
            # Левый пиксель ручки на позиции 15px правой границы трека
            handle_x = track_rect.x + int(track_rect.w * progress) - 15
            handle_y = track_rect.centery - hh // 2
        else:
            handle_x = track_rect.centerx - hw // 2
            handle_y = track_rect.y + int(track_rect.h * progress) - 15

        return pygame.Rect(handle_x, handle_y, hw, hh)