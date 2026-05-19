"""
TerrainGenerator — заполняет чанк тайлами по шуму Перлина и правилам биома.

Добавить новый биом = добавить JSON в data/biomes/, код не трогать.
"""

import json
import math
import random


def _fade(t):
    return t * t * t * (t * (t * 6 - 15) + 10)


def _lerp(a, b, t):
    return a + t * (b - a)


def _grad(h, x, y):
    h = h & 3
    if h == 0: return  x + y
    if h == 1: return -x + y
    if h == 2: return  x - y
    return -x - y


class PerlinNoise:
    """Простой 2D Perlin noise без зависимостей."""

    def __init__(self, seed: int = 0):
        rng = random.Random(seed)
        p = list(range(256))
        rng.shuffle(p)
        self._perm = p * 2

    def noise(self, x: float, y: float) -> float:
        xi = int(math.floor(x)) & 255
        yi = int(math.floor(y)) & 255
        xf = x - math.floor(x)
        yf = y - math.floor(y)
        u = _fade(xf)
        v = _fade(yf)
        p = self._perm
        aa = p[p[xi]     + yi]
        ab = p[p[xi]     + yi + 1]
        ba = p[p[xi + 1] + yi]
        bb = p[p[xi + 1] + yi + 1]
        x1 = _lerp(_grad(aa, xf,     yf),     _grad(ba, xf - 1, yf),     u)
        x2 = _lerp(_grad(ab, xf,     yf - 1), _grad(bb, xf - 1, yf - 1), u)
        return (_lerp(x1, x2, v) + 1) / 2  # нормализуем 0..1


class TerrainGenerator:
    def __init__(self, gen_config_path: str, biomes_dir: str):
        with open(gen_config_path, encoding="utf-8") as f:
            cfg = json.load(f)

        self._seed = cfg["seed"]
        self._chunk_size = cfg["chunk_size"]
        self._scale = cfg["noise"]["scale"]
        self._octaves = cfg["noise"]["octaves"]
        self._persistence = cfg["noise"]["persistence"]
        self._lacunarity = cfg["noise"]["lacunarity"]

        biome_id = cfg["biome"]
        biome_path = f"{biomes_dir}/{biome_id}.json"
        with open(biome_path, encoding="utf-8") as f:
            biome = json.load(f)

        self._terrain_rules = biome["terrain_rules"]
        self._noise = PerlinNoise(seed=self._seed)

        print(f"[TerrainGenerator] seed={self._seed}, biome={biome_id}, "
              f"scale={self._scale}, octaves={self._octaves}")

    def fill_chunk(self, chunk) -> None:
        """
        Заполняет chunk.logical_grid тайлами.
        chunk_x, chunk_y — координаты чанка в чанковом пространстве.
        """
        ox = chunk.chunk_x * chunk.size
        oy = chunk.chunk_y * chunk.size

        for y in range(chunk.size):
            for x in range(chunk.size):
                wx = (ox + x) * self._scale
                wy = (oy + y) * self._scale

                noise_val = self._octave_noise(wx, wy)
                tile_id = self._apply_rules(noise_val)
                chunk.logical_grid[y][x] = tile_id

        chunk.mark_all_dirty()

    def _octave_noise(self, x: float, y: float) -> float:
        value = 0.0
        amplitude = 1.0
        frequency = 1.0
        max_value = 0.0

        for _ in range(self._octaves):
            value += self._noise.noise(x * frequency, y * frequency) * amplitude
            max_value += amplitude
            amplitude *= self._persistence
            frequency *= self._lacunarity

        return value / max_value  # нормализуем 0..1

    def _apply_rules(self, noise_val: float) -> str:
        """Правила из biome JSON: первое совпадение побеждает."""
        for rule in self._terrain_rules:
            if noise_val <= rule["noise_max"]:
                return rule["tile"]
        return self._terrain_rules[-1]["tile"]  # fallback
