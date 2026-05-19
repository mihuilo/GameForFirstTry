"""
DecorationGenerator — расставляет декоративные тайлы поверх terrain.
"""

import os
import json


class DecorationGenerator:
    def __init__(self, tiles_dir: str):
        self._rules: list[dict] = []
        self._load_rules(tiles_dir)

    def _load_rules(self, tiles_dir: str):
        for filename in os.listdir(tiles_dir):
            if not filename.endswith(".json"):
                continue
            with open(os.path.join(tiles_dir, filename), encoding="utf-8") as f:
                data = json.load(f)
            if data.get("layer") == "decoration":
                self._rules.append(data)

    def fill_chunk(self, chunk, terrain_getter) -> dict[tuple[int, int], str]:
        """
        Возвращает {(local_x, local_y): tile_id} — где ставить декорации.
        terrain_getter(world_x, world_y) → tile_id
        """
        result: dict[tuple[int, int], str] = {}

        for rule in self._rules:
            tile_id = rule["id"]
            spawns_on = set(rule.get("spawns_on", []))
            min_dist = rule.get("min_distance_from", {})

            for y in range(chunk.size):
                for x in range(chunk.size):
                    wx = chunk.chunk_x * chunk.size + x
                    wy = chunk.chunk_y * chunk.size + y

                    # Проверяем что под декорацией нужный тайл
                    if terrain_getter(wx, wy) not in spawns_on:
                        continue

                    # Проверяем дистанцию от запрещённых тайлов
                    if self._check_distance(wx, wy, min_dist, terrain_getter):
                        result[(x, y)] = tile_id

        return result

    def _check_distance(self, wx, wy, min_dist: dict, terrain_getter) -> bool:
        for forbidden_tile, min_d in min_dist.items():
            for dy in range(-min_d, min_d + 1):
                for dx in range(-min_d, min_d + 1):
                    if terrain_getter(wx + dx, wy + dy) == forbidden_tile:
                        return False
        return True