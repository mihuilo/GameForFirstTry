"""
TileRegistry — загружает все логические описания тайлов из data/tiles/.

Использование:
    registry = TileRegistry("data/tiles")
    tile = registry.get("dirt")   # → {"id": "dirt", "walkable": True, ...}

Добавить новый тайл = создать новый JSON файл. Код не трогается.
"""

import json
import os


class TileRegistry:
    def __init__(self, data_dir: str):
        self._tiles: dict[str, dict] = {}
        self._load(data_dir)

    def _load(self, data_dir: str):
        if not os.path.isdir(data_dir):
            raise FileNotFoundError(f"TileRegistry: папка не найдена: {data_dir}")

        for filename in os.listdir(data_dir):
            if not filename.endswith(".json"):
                continue
            path = os.path.join(data_dir, filename)
            with open(path, encoding="utf-8") as f:
                data = json.load(f)

            tile_id = data.get("id")
            if not tile_id:
                raise ValueError(f"TileRegistry: в файле {filename} нет поля 'id'")

            self._tiles[tile_id] = data

        print(f"[TileRegistry] Загружено тайлов: {len(self._tiles)} → {list(self._tiles.keys())}")

    def get(self, tile_id: str) -> dict:
        if tile_id not in self._tiles:
            raise KeyError(f"TileRegistry: тайл '{tile_id}' не найден")
        return self._tiles[tile_id]

    def all(self) -> dict[str, dict]:
        return dict(self._tiles)
