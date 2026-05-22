"""
ObjectRegistry — загружает описания объектов из data/objects/.
"""

import json
import os
import pygame
from rendering.atlas import Atlas


class ObjectRegistry:
    def __init__(self, data_dir: str, tile_size: int = 32):
        self._objects: dict[str, dict] = {}
        self._atlases: dict[str, Atlas] = {}

        self._tile_size = tile_size
        self._load(data_dir)

    def _load(self, data_dir: str):
        if not os.path.isdir(data_dir):
            raise FileNotFoundError(f"ObjectRegistry: папка не найдена: {data_dir}")

        for filename in os.listdir(data_dir):
            if not filename.endswith(".json"):
                continue
            path = os.path.join(data_dir, filename)
            with open(path, encoding="utf-8") as f:
                data = json.load(f)

            # Каждый вариант регистрируем отдельно
            atlas_path = data.get("atlas")
            tile_w = data.get("tile_w", 16)
            tile_h = data.get("tile_h", 16)

            for variant in data.get("variants", []):
                obj_id = variant["id"]
                self._objects[obj_id] = {
                    "scale":        data.get("scale", 1.0),
                    "id":           obj_id,
                    "atlas":        atlas_path,
                    "atlas_index":  variant["atlas_index"],
                    "tile_w":       tile_w,
                    "tile_h":       tile_h,
                    "walkable":     data.get("walkable", False),
                    "spawns_on":    data.get("spawns_on", []),
                    "min_distance_from": data.get("min_distance_from", {}),
                    "spawn_chance": data.get("spawn_chance", 0.05),
                    "interaction":  data.get("interaction", None),
                }

        print(f"[ObjectRegistry] Загружено объектов: {len(self._objects)} → {list(self._objects.keys())}")

    def get(self, obj_id: str) -> dict:
        if obj_id not in self._objects:
            raise KeyError(f"ObjectRegistry: объект '{obj_id}' не найден")
        return self._objects[obj_id]

    def has(self, obj_id: str) -> bool:
        return obj_id in self._objects

    def get_surface(self, obj_id: str) -> pygame.Surface | None:
        obj = self.get(obj_id)
        atlas_path = obj.get("atlas")
        if not atlas_path or not os.path.exists(atlas_path):
            return None

        if atlas_path not in self._atlases:
            self._atlases[atlas_path] = Atlas(
                atlas_path,
                obj["tile_w"],
                obj["tile_h"]
            )

        atlas = self._atlases[atlas_path]
        return atlas.get_by_index(obj["atlas_index"])

    def all_spawnable(self) -> list[dict]:
        """Возвращает все объекты у которых есть spawns_on."""
        return [o for o in self._objects.values() if o.get("spawns_on")]