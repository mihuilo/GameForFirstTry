"""
Button — кнопка с 9-slice спрайтом.
Три состояния: normal, hover, pressed.
"""

import pygame


class Button:
    STATE_POS = {
        "normal":  (0, 0),
        "hover":   (1, 0),
        "pressed": (0, 1),
    }

    def __init__(self, path: str, scale: int = 2, slice_size: int = 8):
        self._sheet  = pygame.image.load(path).convert_alpha()
        self._scale  = scale
        self._slice  = slice_size
        self._btn_w  = slice_size * 3
        self._btn_h  = slice_size * 3
        self._state  = "normal"

    def draw(self, surface: pygame.Surface, rect: pygame.Rect, text: str, font: pygame.font.Font) -> None:
        self._draw_nine_slice(surface, rect)
        txt = font.render(text, True, (240, 210, 160))
        surface.blit(txt, (
            rect.x + rect.w // 2 - txt.get_width() // 2,
            rect.y + rect.h // 2 - txt.get_height() // 2
        ))

    def update(self, event, rect: pygame.Rect) -> bool:
        mx, my = pygame.mouse.get_pos()
        hovered = rect.collidepoint(mx, my)

        if hovered:
            self._state = "hover"
        else:
            if self._state != "pressed":
                self._state = "normal"

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and hovered:
            self._state = "pressed"
            return True

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self._state = "hover" if hovered else "normal"

        return False

    def _draw_nine_slice(self, surface: pygame.Surface, rect: pygame.Rect):
        s_src = self._slice
        s_dst = self._slice * self._scale
        col, row = self.STATE_POS[self._state]
        offset_x = col * self._btn_w
        offset_y = row * self._btn_h

        x, y, w, h = rect.x, rect.y, rect.width, rect.height

        pieces = [
            (0, 0, x,         y,         s_dst,     s_dst    ),
            (2, 0, x+w-s_dst, y,         s_dst,     s_dst    ),
            (0, 2, x,         y+h-s_dst, s_dst,     s_dst    ),
            (2, 2, x+w-s_dst, y+h-s_dst, s_dst,     s_dst    ),
            (1, 0, x+s_dst,   y,         w-s_dst*2, s_dst    ),
            (1, 2, x+s_dst,   y+h-s_dst, w-s_dst*2, s_dst    ),
            (0, 1, x,         y+s_dst,   s_dst,     h-s_dst*2),
            (2, 1, x+w-s_dst, y+s_dst,   s_dst,     h-s_dst*2),
            (1, 1, x+s_dst,   y+s_dst,   w-s_dst*2, h-s_dst*2),
        ]

        for src_col, src_row, dx, dy, dw, dh in pieces:
            src = pygame.Rect(offset_x + src_col * s_src, offset_y + src_row * s_src, s_src, s_src)
            tile = pygame.Surface((s_src, s_src), pygame.SRCALPHA)
            tile.blit(self._sheet, (0, 0), src)
            scaled = pygame.transform.scale(tile, (max(1, dw), max(1, dh)))
            surface.blit(scaled, (dx, dy))