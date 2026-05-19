"""
TilesetRegistry — загружает правила autotile из data/tilesets/.

Для autotile-тайлов хранит маппинг: bitmask (int) → sprite filename.
Для solid_color тайлов хранит цвет.

Использование:
    registry = TilesetRegistry("data/tilesets", "assets/tiles")
    sprite_name = registry.get_sprite("dirt", bitmask=6)   # → "tile_dirt_0001.png"
    color       = registry.get_color("water")               # → (30, 100, 200)
"""

import json
import os



class TilesetRegistry:
    def __init__(self, data_dir: str, assets_dir: str):
        self._tilesets: dict[str, dict] = {}
        self._assets_dir = assets_dir
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

            # Для autotile: подготовим bitmask_map с int-ключами
            if data.get("type") == "4bit_autotile":
                raw_map = data.get("bitmask_map", {})
                data["_bitmask_map"] = {
                    int(k): v
                    for k, v in raw_map.items()
                    if k != "comment" and k != "comment2"
                }

            self._tilesets[ts_id] = data

        print(f"[TilesetRegistry] Загружено тайлсетов: {len(self._tilesets)} → {list(self._tilesets.keys())}")

    def get_sprite_path(self, tileset_id: str, bitmask: int):
        """
        Для sprite_prefix → возвращает str (путь к файлу).
        Для atlas → возвращает tuple (путь к атласу, индекс).
        """
        ts = self._get(tileset_id)
        if ts.get("type") != "4bit_autotile":
            raise TypeError(f"TilesetRegistry: '{tileset_id}' не является autotile")

        bitmask = max(0, min(15, bitmask))
        sprite_id = ts["_bitmask_map"].get(bitmask)
        if sprite_id is None:
            raise KeyError(f"TilesetRegistry: нет маппинга для bitmask={bitmask} в '{tileset_id}'")

        # Атлас — возвращаем (путь, индекс)
        if "atlas" in ts:
            atlas_path = ts["atlas"]
            index = int(sprite_id)
            return (atlas_path, index)

        # Отдельные файлы — возвращаем путь
        prefix = ts.get("sprite_prefix", "")
        filename = f"{prefix}{sprite_id}.png"
        return os.path.join(self._assets_dir, filename)

    def get_color(self, tileset_id: str) -> tuple[int, int, int]:
        """
        Возвращает (R, G, B) для solid_color тайлсетов.
        """
        ts = self._get(tileset_id)
        if ts.get("type") != "solid_color":
            raise TypeError(f"TilesetRegistry: '{tileset_id}' не является solid_color")
        return tuple(ts["color"])

    def get_type(self, tileset_id: str) -> str:
        return self._get(tileset_id).get("type", "unknown")

    def get_connects_to(self, tileset_id: str) -> list[str]:
        """Список tile_id, с которыми этот тайл 'сливается' при autotile."""
        return self._get(tileset_id).get("connects_to", [tileset_id])

    def _get(self, tileset_id: str) -> dict:
        if tileset_id not in self._tilesets:
            raise KeyError(f"TilesetRegistry: тайлсет '{tileset_id}' не найден")
        return self._tilesets[tileset_id]

