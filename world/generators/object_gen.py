"""
ObjectGenerator — расставляет объекты по миру.
"""

import random
from world.object_registry import ObjectRegistry


class ObjectGenerator:
    def __init__(self, object_registry: ObjectRegistry, seed: int = 42):
        self._registry = object_registry
        self._seed = seed

    def fill_chunk(self, chunk, terrain_getter) -> dict[tuple[int, int], str]:
        rng = random.Random(
            self._seed ^ (chunk.chunk_x * 92837111) ^ (chunk.chunk_y * 689287499)
        )
        result: dict[tuple[int, int], str] = {}

        # Кешируем terrain один раз
        terrain_cache = {}
        for y in range(chunk.size):
            for x in range(chunk.size):
                wx = chunk.chunk_x * chunk.size + x
                wy = chunk.chunk_y * chunk.size + y
                terrain_cache[(x, y)] = terrain_getter(wx, wy)

        spawnable = self._registry.all_spawnable()

        for y in range(chunk.size):
            for x in range(chunk.size):
                if (x, y) in result:
                    continue

                tile = terrain_cache[(x, y)]

                for obj_def in spawnable:
                    if tile not in obj_def.get("spawns_on_set", set(obj_def.get("spawns_on", []))):
                        continue

                    min_obj_dist = obj_def.get("min_distance_objects", 2)
                    if any(
                            (x + dx, y + dy) in result
                            for dx in range(-min_obj_dist, min_obj_dist + 1)
                            for dy in range(-min_obj_dist, min_obj_dist + 1)
                    ):
                        continue

                    wx = chunk.chunk_x * chunk.size + x
                    wy = chunk.chunk_y * chunk.size + y
                    if not self._check_distance(wx, wy, obj_def.get("min_distance_from", {}), terrain_getter):
                        continue

                    if rng.random() < obj_def.get("spawn_chance", 0.05):
                        result[(x, y)] = obj_def["id"]
                        break  # одна клетка — один объект, дальше не проверяем

        return result

    def _check_distance(self, wx, wy, min_dist: dict, terrain_getter) -> bool:
        for forbidden, min_d in min_dist.items():
            for dy in range(-min_d, min_d + 1):
                for dx in range(-min_d, min_d + 1):
                    if terrain_getter(wx + dx, wy + dy) == forbidden:
                        return False
        return True