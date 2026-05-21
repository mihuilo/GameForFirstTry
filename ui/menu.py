"""
Menu — меню паузы (ESC).
"""

import pygame
from ui.nine_slice import NineSlice
from ui.button import Button
from ui.slider import Slider
from ui.blocks import (LabelBlock, HintBlock, SliderBlock,
                       TabBlock, ButtonRowBlock, ExitButtonBlock)

PANEL_SIZES = {
    "small":  (700,  420),
    "medium": (1000, 600),
    "large":  (1300, 910),
}

TABS = ["Графика", "Звук"]


class PauseMenu:
    ZOOM_MIN = 70
    ZOOM_MAX = 120
    BORDER   = 18 * 5

    def __init__(self, panel_path: str = "assets/ui/panel.png",
                 button_path: str = "assets/ui/button.png"):
        self.active        = False
        self._zoom_percent = 90
        self._ui_size      = "small"
        self._scroll_offset = 0
        self._should_exit  = False

        self._nine_slice = NineSlice(panel_path, scale=5)

        # Scroll area rect — заполняется в draw()
        self._scroll_rect: pygame.Rect = None

        # Вкладки
        self._tab_block = TabBlock(TABS, button_path,
                                   on_change=lambda t: self._on_tab_change(t))
        self._active_tab = TABS[0]

        # Кнопка выхода
        self._exit_block = ExitButtonBlock(button_path,
                                           on_exit=lambda: setattr(self, '_should_exit', True))

        # Кнопки размера интерфейса
        self._size_block = ButtonRowBlock(
            label="Размер интерфейса:",
            options={"small": "Маленький", "medium": "Средний", "large": "Большой"},
            button_path=button_path,
            active_getter=lambda: self._ui_size,
            on_change=lambda k: setattr(self, '_ui_size', k)
        )

        # Блоки вкладки Графика
        zoom_slider = Slider("assets/ui/slider_h.png", scale=3,
                             min_val=70, max_val=120, orientation="horizontal")
        self._tab_blocks = {
            "Графика": [
                LabelBlock(lambda: f"Масштаб мира: {self._zoom_percent}%"),
                SliderBlock(zoom_slider, on_change=lambda v: setattr(self, '_zoom_percent', v)),
                HintBlock("70%", "120%"),
                self._size_block,
            ],
            "Звук": [
                LabelBlock("Настройки звука — в разработке"),
            ],
        }

        # Адаптируем scale слайдера при смене размера панели
        self._zoom_slider = zoom_slider

    def _on_tab_change(self, tab: str):
        self._active_tab = tab
        self._scroll_offset = 0  # сбрасываем скролл при смене вкладки

    @property
    def zoom(self) -> float:
        return self._zoom_percent / 100.0

    def toggle(self):
        self.active = not self.active
        self._scroll_offset = 0

    def handle_event(self, event) -> bool:
        if not self.active:
            return False

        self._should_exit = False

        # Вкладки
        self._tab_block.handle_event(event)
        self._active_tab = self._tab_block.active

        # Фиксированные блоки снизу
        self._size_block.handle_event(event)
        self._exit_block.handle_event(event)

        if self._should_exit:
            return True

        # Скролл колёсиком
        if event.type == pygame.MOUSEWHEEL:
            if self._scroll_rect and self._scroll_rect.collidepoint(pygame.mouse.get_pos()):
                self._scroll_offset -= event.y * 20
                self._scroll_offset = max(0, self._scroll_offset)

        # Блоки активной вкладки
        for block in self._tab_blocks.get(self._active_tab, []):
            block.handle_event(event)

        # Блоки активной вкладки — передаём смещение
        scroll_origin_y = self._scroll_rect.y if self._scroll_rect else 0
        scroll_origin_x = self._scroll_rect.x if self._scroll_rect else 0

        offset_x = self._scroll_rect.x if self._scroll_rect else 0
        offset_y = self._scroll_rect.y - self._scroll_offset if self._scroll_rect else 0

        for block in self._tab_blocks.get(self._active_tab, []):
            if isinstance(block, (SliderBlock, ButtonRowBlock)):
                block.handle_event(event, offset_x, offset_y)
            else:
                block.handle_event(event)

        return False

    def draw(self, surface: pygame.Surface):
        if not self.active:
            return

        sw, sh = surface.get_size()
        panel_w, panel_h = PANEL_SIZES[self._ui_size]
        panel_x = sw // 2 - panel_w // 2
        panel_y = sh // 2 - panel_h // 2

        title_size = max(16, panel_h // 13)
        label_size = max(12, panel_h // 20)
        font_title = pygame.font.SysFont("monospace", title_size, bold=True)
        font       = pygame.font.SysFont("monospace", label_size)

        pad = self.BORDER

        # Адаптируем scale слайдера
        self._zoom_slider._scale = max(1, panel_h // 140)

        # Затемнение
        overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        surface.blit(overlay, (0, 0))

        # Панель
        self._nine_slice.draw(surface, pygame.Rect(panel_x, panel_y, panel_w, panel_h))

        # Заголовок
        title = font_title.render("Настройки", True, (80, 40, 10))
        surface.blit(title, (panel_x + panel_w // 2 - title.get_width() // 2,
                              panel_y + pad // 2))

        content_x = panel_x + pad
        content_w = panel_w - pad * 2

        # Вкладки — фиксированные
        tab_y = panel_y + pad // 2 + title_size
        tab_y = self._tab_block.draw(surface, content_x, tab_y, content_w, font)

        # Фиксированная зона снизу
        size_btn_h = label_size + 16
        # Фиксированная зона снизу — только кнопка выхода
        exit_btn_h = label_size + 16   # высота кнопки с запасом
        bottom_h = exit_btn_h + 20  # + небольшой отступ
        bottom_y = panel_y + panel_h - pad - exit_btn_h

        # Scroll area между вкладками и низом
        scroll_area_y = tab_y + 4
        scroll_area_h = bottom_y - scroll_area_y - 8
        self._scroll_rect = pygame.Rect(content_x, scroll_area_y, content_w, scroll_area_h)

        # Рисуем содержимое вкладки в scroll area
        self._draw_scroll_content(surface, font)

        # Разделитель
        pygame.draw.line(surface, (160, 100, 50),
                         (content_x, bottom_y),
                         (content_x + content_w, bottom_y), 2)

        # Фиксированные блоки снизу
        y = bottom_y + 8
        self._exit_block.draw(surface, content_x, y, content_w, font)

    def _draw_scroll_content(self, surface: pygame.Surface, font: pygame.font.Font):
        if not self._scroll_rect:
            return

        # Считаем полную высоту контента
        blocks = self._tab_blocks.get(self._active_tab, [])
        dummy = pygame.Surface((1, 1), pygame.SRCALPHA)
        total_h = 0
        for block in blocks:
            total_h = block.draw(dummy, 0, total_h, self._scroll_rect.width, font)

        # Ограничиваем скролл
        max_scroll = max(0, total_h - self._scroll_rect.height)
        self._scroll_offset = min(self._scroll_offset, max_scroll)

        # Рисуем на временной поверхности нужного размера
        content_surf = pygame.Surface(
            (self._scroll_rect.width, max(total_h, self._scroll_rect.height)),
            pygame.SRCALPHA
        )
        y = 0
        for block in blocks:
            y = block.draw(content_surf, 0, y, self._scroll_rect.width, font)

        # Вырезаем нужный кусок и рисуем
        clip_rect = pygame.Rect(0, self._scroll_offset, self._scroll_rect.width, self._scroll_rect.height)
        old_clip = surface.get_clip()
        surface.set_clip(self._scroll_rect)
        surface.blit(content_surf, (self._scroll_rect.x, self._scroll_rect.y), clip_rect)
        surface.set_clip(old_clip)

        # Ручки слайдеров рисуем БЕЗ обрезки поверх всего
        for block in blocks:
            if isinstance(block, SliderBlock):
                block.draw_handle(surface,
                                  self._scroll_rect.x,
                                  self._scroll_rect.y - self._scroll_offset)

        # Скроллбар
        if total_h > self._scroll_rect.height:
            self._draw_scrollbar(surface, total_h)

        # Скроллбар
        if total_h > self._scroll_rect.height:
            self._draw_scrollbar(surface, total_h)

    def _draw_scrollbar(self, surface: pygame.Surface, total_h: int):
        r = self._scroll_rect
        bar_w = 6
        bar_x = r.x + r.width - bar_w

        ratio    = r.height / total_h
        bar_h    = max(20, int(r.height * ratio))
        bar_y    = r.y + int((self._scroll_offset / total_h) * r.height)

        pygame.draw.rect(surface, (160, 100, 50),
                         pygame.Rect(bar_x, r.y, bar_w, r.height), border_radius=3)
        pygame.draw.rect(surface, (220, 160, 80),
                         pygame.Rect(bar_x, bar_y, bar_w, bar_h), border_radius=3)