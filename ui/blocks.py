"""
blocks.py — компонентные блоки UI.
Каждый блок знает свой размер и умеет себя рисовать.
Меню просто складывает их вертикально.
"""

import pygame
from ui.button import Button
from ui.slider import Slider


class Block:
    """Базовый класс блока."""
    GAP = 8  # отступ между блоками

    def draw(self, surface: pygame.Surface, x: int, y: int, width: int, font: pygame.font.Font) -> int:
        """Рисует блок. Возвращает y после блока."""
        raise NotImplementedError

    def handle_event(self, event) -> None:
        pass


class LabelBlock(Block):
    """Просто текст."""

    def __init__(self, text_getter, color: tuple = (80, 40, 10)):
        # text_getter — строка или callable который возвращает строку
        self._text_getter = text_getter
        self._color = color

    def draw(self, surface, x, y, width, font) -> int:
        text = self._text_getter() if callable(self._text_getter) else self._text_getter
        label = font.render(text, True, self._color)
        surface.blit(label, (x, y))
        return y + label.get_height() + int(font.size("A")[1] * 0.6)


class HintBlock(Block):
    """Два текста по краям — например '70%' и '120%'."""

    def __init__(self, left: str, right: str, color: tuple = (100, 60, 20)):
        self._left  = left
        self._right = right
        self._color = color

    def draw(self, surface, x, y, width, font) -> int:
        left_lbl  = font.render(self._left,  True, self._color)
        right_lbl = font.render(self._right, True, self._color)
        surface.blit(left_lbl,  (x, y))
        surface.blit(right_lbl, (x + width - right_lbl.get_width(), y))
        return y + left_lbl.get_height() + self.GAP


class SliderBlock(Block):
    """Ползунок."""

    def __init__(self, slider: Slider, on_change=None):
        self._slider   = slider
        self._on_change = on_change  # callback(value) при изменении
        self._track_rect = None

    def handle_event(self, event, offset_x: int = 0, offset_y: int = 0) -> None:
        if self._track_rect:
            adjusted = self._track_rect.move(offset_x, offset_y)
            if self._slider.handle_event(event, adjusted):
                if self._on_change:
                    self._on_change(self._slider.value)

    def draw(self, surface, x, y, width, font) -> int:
        track_h = 4
        self._track_rect = pygame.Rect(x, y, width, track_h)
        self._slider.draw(surface, self._track_rect)
        gap = font.size("A")[1] * 0.6  # отступ пропорционален размеру шрифта
        return y + track_h + gap

    def draw_handle(self, surface: pygame.Surface, offset_x: int, offset_y: int):
        """Рисует только ручку слайдера поверх всего."""
        if not self._track_rect:
            return
        adjusted = self._track_rect.move(offset_x, offset_y)
        hw = self._slider._handle_w * self._slider._scale
        hh = self._slider._handle_h * self._slider._scale
        progress = (self._slider.value - self._slider._min) / (self._slider._max - self._slider._min)
        handle_x = adjusted.x + int(adjusted.w * progress) - 15
        handle_y = adjusted.centery - hh // 2
        handle_surf = pygame.transform.scale(self._slider._sheet, (hw, hh))
        surface.blit(handle_surf, (handle_x, handle_y))

class CheckboxBlock(Block):
    """Чекбокс с подписью."""

    def __init__(self, label: str, value: bool = False, on_change=None):
        self._label     = label
        self._value     = value
        self._on_change = on_change
        self._rect      = None

    @property
    def value(self) -> bool:
        return self._value

    def handle_event(self, event, offset_x: int = 0, offset_y: int = 0) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self._rect:
                adjusted = self._rect.move(offset_x, offset_y)
                if adjusted.collidepoint(event.pos):
                    self._value = not self._value
                    if self._on_change:
                        self._on_change(self._value)

    def draw(self, surface, x, y, width, font) -> int:
        size = font.size("A")[1]
        self._rect = pygame.Rect(x, y, size, size)

        # Квадрат
        pygame.draw.rect(surface, (160, 100, 50), self._rect, border_radius=3)
        if self._value:
            inner = self._rect.inflate(-4, -4)
            pygame.draw.rect(surface, (80, 40, 10), inner, border_radius=2)

        # Подпись
        lbl = font.render(self._label, True, (80, 40, 10))
        surface.blit(lbl, (x + size + 8, y))

        return y + size + self.GAP

class TabBlock(Block):
    """Вкладки."""

    def __init__(self, tabs: list[str], button_path: str, on_change=None):
        self._tabs      = tabs
        self._active    = tabs[0]
        self._on_change = on_change
        self._btns      = {tab: Button(button_path, scale=3) for tab in tabs}
        self._rects:    dict[str, pygame.Rect] = {}

    @property
    def active(self) -> str:
        return self._active

    def handle_event(self, event) -> None:
        for tab, rect in self._rects.items():
            if self._btns[tab].update(event, rect):
                self._active = tab
                if self._on_change:
                    self._on_change(tab)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for tab, rect in self._rects.items():
                if rect.collidepoint(event.pos):
                    self._active = tab

    def draw(self, surface, x, y, width, font) -> int:
        tab_w = width // len(self._tabs)
        tab_h = font.size("A")[1] + 16
        self._rects = {}
        for i, tab in enumerate(self._tabs):
            rect = pygame.Rect(x + i * tab_w, y, tab_w - 4, tab_h)
            self._rects[tab] = rect
            if tab == self._active:
                self._btns[tab]._state = "pressed"
            elif self._btns[tab]._state != "hover":
                self._btns[tab]._state = "normal"
            self._btns[tab].draw(surface, rect, tab, font)
        return y + tab_h + self.GAP


class ButtonRowBlock(Block):
    """Ряд кнопок с подписью сверху."""

    def __init__(self, label: str, options: dict[str, str],
                 button_path: str, active_getter, on_change=None):
        """
        options     — {key: label} например {"small": "Маленький"}
        active_getter — callable который возвращает текущий активный key
        """
        self._label       = label
        self._options     = options
        self._active_getter = active_getter
        self._on_change   = on_change
        self._btns        = {key: Button(button_path, scale=3) for key in options}
        self._rects:      dict[str, pygame.Rect] = {}

    def handle_event(self, event, offset_x: int = 0, offset_y: int = 0) -> None:
        adjusted_rects = {
            key: rect.move(offset_x, offset_y)
            for key, rect in self._rects.items()
        }
        for key, rect in adjusted_rects.items():
            if self._btns[key].update(event, rect):
                if self._on_change:
                    self._on_change(key)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for key, rect in adjusted_rects.items():
                if rect.collidepoint(event.pos):
                    if self._on_change:
                        self._on_change(key)

    def draw(self, surface, x, y, width, font) -> int:
        lbl = font.render(self._label, True, (80, 40, 10))
        surface.blit(lbl, (x, y))
        y += lbl.get_height() + 4

        btn_w = width // len(self._options)
        btn_h = font.size("A")[1] + 16
        gap = max(2, btn_w // 20)  # отступ пропорционален ширине кнопки
        self._rects = {}
        active = self._active_getter()
        for i, (key, label) in enumerate(self._options.items()):
            rect = pygame.Rect(x + i * btn_w + gap, y, btn_w - gap * 2, btn_h)
            self._rects[key] = rect
            if key == active:
                self._btns[key]._state = "pressed"
            elif self._btns[key]._state != "hover":
                self._btns[key]._state = "normal"
            self._btns[key].draw(surface, rect, label, font)

        return y + btn_h + self.GAP


class ExitButtonBlock(Block):
    """Кнопка выхода."""

    def __init__(self, button_path: str, on_exit=None):
        self._btn     = Button(button_path, scale=3)
        self._on_exit = on_exit
        self._rect    = None

    def handle_event(self, event) -> None:
        if self._rect:
            if self._btn.update(event, self._rect):
                if self._on_exit:
                    self._on_exit()

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self._rect and self._rect.collidepoint(event.pos):
                if self._on_exit:
                    self._on_exit()

    def draw(self, surface, x, y, width, font) -> int:
        btn_w = width // 2
        btn_h = font.size("A")[1] + 20
        self._rect = pygame.Rect(x + width // 2 - btn_w // 2, y, btn_w, btn_h)
        self._btn.draw(surface, self._rect, "Выйти из игры", font)
        return y + btn_h + self.GAP