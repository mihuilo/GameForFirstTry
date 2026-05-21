"""
TilesetRegistry — загружает правила autotile из data/tilesets/.
Сам создаёт Atlas и отдаёт готовый Surface — рендер не знает про форматы.
"""

import json
import os
import pygame
from rendering.atlas import Atlas


class TilesetRegistry:
    def __init__(self, data_dir: str, assets_dir: str, tile_size: int = 32):
        self._tilesets: dict[str, dict] = {}
        self._atlases: dict[str, Atlas] = {}
        self._assets_dir = assets_dir
        self._tile_size = tile_size
        self._load(data_dir)

    def _load(self, data_dir: str):
        if not os.path.isdir(data_dir):
            raise FileNotFoundError(f"TilesetRegistry: папка не найдена: {data_dir}")

        for filename in os.listdir(data_dir):
            if not filename.endswith(".json"):
                continue
            path = os.path.join(data_dir, filename)
            with open(path, encoding="utf-8") as f:
                data = json.load(f)

            ts_id = data.get("id")
            if not ts_id:
                raise ValueError(f"TilesetRegistry: в файле {filename} нет поля 'id'")

            if data.get("type") == "4bit_autotile":
                raw_map = data.get("bitmask_map", {})
                data["_bitmask_map"] = {
                    int(k): v
                    for k, v in raw_map.items()
                    if k not in ("comment", "comment2")
                }

            if data.get("type") == "8bit_autotile":
                raw_map = data.get("bitmask_map", {})
                parsed = {}
                for k, v in raw_map.items():
                    try:
                        parsed[int(k)] = v
                    except ValueError:
                        pass
                data["_bitmask_map"] = parsed

            self._tilesets[ts_id] = data

        print(f"[TilesetRegistry] Загружено тайлсетов: {len(self._tilesets)} → {list(self._tilesets.keys())}")

    def _get_atlas(self, ts: dict) -> Atlas | None:
        atlas_path = ts.get("atlas")
        if not atlas_path:
            return None

        if atlas_path not in self._atlases:
            tile_w = ts.get("tile_size", 16)
            tile_h = ts.get("tile_size", 16)
            self._atlases[atlas_path] = Atlas(atlas_path, tile_w, tile_h, scale_to=self._tile_size)

        return self._atlases[atlas_path]
    def get_surface(self, tileset_id: str, bitmask: int, world_x: int = 0, world_y: int = 0) -> pygame.Surface | None:
        """Возвращает готовый Surface для тайла по bitmask."""
        ts = self._get(tileset_id)


        if ts.get("type") not in ("4bit_autotile", "8bit_autotile"):
            return None

        sprite_id = ts["_bitmask_map"].get(bitmask)
        if sprite_id is None:
            return None

        # Вариативность по координатам
        if isinstance(sprite_id, list):
            index = (world_x * 7 + world_y * 13) % len(sprite_id)
            sprite_id = sprite_id[index]


        if isinstance(sprite_id, list):
            index = (world_x * 7 + world_y * 13) % len(sprite_id)
            sprite_id = sprite_id[index]

        if not sprite_id:
            return None

        index = int(sprite_id)

        # Атлас
        atlas = self._get_atlas(ts)
        if atlas:
            return atlas.get_by_index(index)

        # Отдельные файлы
        prefix = ts.get("sprite_prefix", "")
        filename = f"{prefix}{str(index).zfill(4)}.png"
        path = os.path.join(self._assets_dir, filename)
        if not os.path.exists(path):
            return None
        img = pygame.image.load(path).convert_alpha()

        index = int(sprite_id)
        return pygame.transform.scale(img, (self._tile_size, self._tile_size))

    def get_color(self, tileset_id: str) -> tuple[int, int, int] | None:
        ts = self._get(tileset_id)
        if ts.get("type") != "solid_color":
            return None
        return tuple(ts["color"])

    def get_type(self, tileset_id: str) -> str:
        return self._get(tileset_id).get("type", "unknown")

    def get_connects_to(self, tileset_id: str) -> list[str]:
        return self._get(tileset_id).get("connects_to", [tileset_id])

    def has(self, tileset_id: str) -> bool:
        return tileset_id in self._tilesets

    def _get(self, tileset_id: str) -> dict:
        if tileset_id not in self._tilesets:
            raise KeyError(f"TilesetRegistry: тайлсет '{tileset_id}' не найден")
        return self._tilesets[tileset_id]