"""
Player — персонаж игрока.
"""

import pygame
import os


class Animation:
    def __init__(self, frames: list[pygame.Surface], fps: float = 8):
        self.frames = frames
        self.fps = fps
        self._timer = 0.0
        self._index = 0

    def update(self, dt: float):
        self._timer += dt
        if self._timer >= 1.0 / self.fps:
            self._timer = 0.0
            self._index = (self._index + 1) % len(self.frames)

    def current(self) -> pygame.Surface:
        return self.frames[self._index]

    def reset(self):
        self._timer = 0.0
        self._index = 0


class Player:
    SPEED = 120

    def __init__(self, sprites_dir: str, tile_size: int, tile_registry, world_tile_size: int = 32, obj_registry=None):
        self.tile_size = tile_size
        self._world_tile_size = world_tile_size
        self._tile_registry = tile_registry
        self._obj_registry = obj_registry

        self.x = 0.0
        self.y = 0.0

        self.direction = "down"
        self.moving = False

        self._animations = self._load_animations(sprites_dir, tile_size)
        self._current_anim = self._animations["idle_down"]

    def _load_animations(self, sprites_dir: str, tile_size: int) -> dict[str, Animation]:
        anims = {}

        def load(filename) -> list[pygame.Surface]:
            path = os.path.join(sprites_dir, filename)
            if not os.path.exists(path):
                print(f"[Player] Спрайт не найден: {path}")
                return [pygame.Surface((tile_size, tile_size), pygame.SRCALPHA)]
            sheet = pygame.image.load(path).convert_alpha()
            h = sheet.get_height()
            frame_w = sheet.get_width() // 8  # 768 / 8 = 96
            count = sheet.get_width() // frame_w
            frames = []
            for i in range(count):
                surf = pygame.Surface((frame_w, h), pygame.SRCALPHA)
                surf.blit(sheet, (0, 0), pygame.Rect(i * frame_w, 0, frame_w, h))
                scaled = pygame.transform.scale(surf, (tile_size, tile_size))
                frames.append(scaled)
            return frames

        anims["idle_down"] = Animation(load("idle/idle_down.png"), fps=8)
        anims["idle_up"] = Animation(load("idle/idle_up.png"), fps=8)
        anims["idle_right"] = Animation(load("idle/idle_right.png"), fps=8)
        anims["idle_left"] = Animation(load("idle/idle_left.png"), fps=8)

        anims["run_down"] = Animation(load("run/run_down.png"), fps=10)
        anims["run_up"] = Animation(load("run/run_up.png"), fps=10)
        anims["run_left"] = Animation(load("run/run_left.png"), fps=10)
        anims["run_right"] = Animation(load("run/run_right.png"), fps=10)

        return anims

    def update(self, dt, keys, get_tile_at, get_object_at=None):
        dx = dy = 0

        if keys[pygame.K_LEFT]  or keys[pygame.K_a]: dx -= 1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: dx += 1
        if keys[pygame.K_UP]    or keys[pygame.K_w]: dy -= 1
        if keys[pygame.K_DOWN]  or keys[pygame.K_s]: dy += 1

        if dx < 0:   self.direction = "left"
        elif dx > 0: self.direction = "right"
        elif dy < 0: self.direction = "up"
        elif dy > 0: self.direction = "down"

        self.moving = dx != 0 or dy != 0

        speed = self.SPEED * dt
        if dx != 0 and dy != 0:
            speed *= 0.707

        if dx != 0:
            self._move(dx * speed, 0, get_tile_at, get_object_at)
        if dy != 0:
            self._move(0, dy * speed, get_tile_at, get_object_at)

        state = "run" if self.moving else "idle"
        anim_key = f"{state}_{self.direction}"
        if self._current_anim is not self._animations[anim_key]:
            self._current_anim = self._animations[anim_key]
            self._current_anim.reset()

        self._current_anim.update(dt)

    def _move(self, dx: float, dy: float, get_tile_at, get_object_at=None):
        new_x = self.x + dx
        new_y = self.y + dy
        ts = self.tile_size
        wts = self._world_tile_size

        hb_size = self._world_tile_size - 2
        hb_x = new_x + ts / 2 - hb_size / 2
        hb_y = new_y + ts - hb_size * 2 - 8

        points = [
            (hb_x, hb_y),
            (hb_x + hb_size, hb_y),
            (hb_x, hb_y + hb_size),
            (hb_x + hb_size, hb_y + hb_size),
        ]

        for px, py in points:
            tile_x = int(px // wts)
            tile_y = int(py // wts)

            if not self._is_walkable(get_tile_at(tile_x, tile_y)):
                return

            if get_object_at:
                obj_id = get_object_at(tile_x, tile_y)
                if not self._is_object_walkable(obj_id):
                    return

        self.x = new_x
        self.y = new_y

    def _is_object_walkable(self, obj_id: str) -> bool:
        if not obj_id:
            return True
        try:
            return self._obj_registry.get(obj_id).get("walkable", True)
        except KeyError:
            return True


    def _is_walkable(self, tile_id: str) -> bool:
        if not tile_id:
            return False
        try:
            tile_def = self._tile_registry.get(tile_id)
            return tile_def.get("walkable", False)
        except KeyError:
            return False

    def draw(self, surface: pygame.Surface, camera_x: float, camera_y: float):
        frame = self._current_anim.current()
        px = int(self.x - camera_x)
        py = int(self.y - camera_y)
        surface.blit(frame, (px, py))

    def get_camera_target(self, screen_w: int, screen_h: int) -> tuple[float, float]:
        cam_x = self.x + self.tile_size / 2 - screen_w / 2
        cam_y = self.y + self.tile_size / 2 - screen_h / 2
        return cam_x, cam_y