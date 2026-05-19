"""
Chunk — кусок мира размером chunk_size × chunk_size тайлов.

Хранит:
  - logical_grid: что тут логически (tile_id строкой)
  - visual_cache: bitmask для каждой клетки (вычисляется AutoTiler-ом)
  - dirty_cells: клетки, у которых visual_cache устарел

Важно: visual_cache НЕ хранит пути к спрайтам — только bitmask.
Рендер сам запрашивает спрайт у TilesetRegistry по (tile_id, bitmask).
Это позволяет менять спрайты, не трогая логику мира.
"""


class Chunk:
    def __init__(self, chunk_x: int, chunk_y: int, size: int):
        self.chunk_x = chunk_x
        self.chunk_y = chunk_y
        self.size = size

        # Логическая сетка: список строк, каждая строка — список tile_id
        self.logical_grid: list[list[str]] = [
            ["" for _ in range(size)] for _ in range(size)
        ]

        # Визуальный кеш: bitmask для каждой клетки (-1 = не вычислен)
        self.visual_cache: list[list[int]] = [
            [-1 for _ in range(size)] for _ in range(size)
        ]

        # Какие клетки нужно пересчитать
        self._dirty: set[tuple[int, int]] = set()

        # Кеш поверхности чанка
        self.cached_surface = None
        self.surface_dirty = True

    def set_tile(self, local_x: int, local_y: int, tile_id: str):
        """Поставить тайл. Автоматически помечает клетку и соседей как dirty."""
        self.logical_grid[local_y][local_x] = tile_id
        self._mark_dirty(local_x, local_y)

    def get_tile(self, local_x: int, local_y: int) -> str:
        return self.logical_grid[local_y][local_x]

    def set_bitmask(self, local_x: int, local_y: int, bitmask: int):
        self.visual_cache[local_y][local_x] = bitmask
        self._dirty.discard((local_x, local_y))

    def get_bitmask(self, local_x: int, local_y: int) -> int:
        return self.visual_cache[local_y][local_x]

    def mark_all_dirty(self):
        for y in range(self.size):
            for x in range(self.size):
                self._dirty.add((x, y))

    def get_dirty_cells(self) -> set[tuple[int, int]]:
        return set(self._dirty)

    def is_dirty(self) -> bool:
        return len(self._dirty) > 0

    def _mark_dirty(self, x: int, y: int):
        """Помечаем клетку и её 4 соседей как dirty (они тоже меняют bitmask)."""
        for dx, dy in [(0, 0), (0, -1), (1, 0), (0, 1), (-1, 0)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < self.size and 0 <= ny < self.size:
                self._dirty.add((nx, ny))

    def world_to_local(self, world_x: int, world_y: int) -> tuple[int, int]:
        return world_x - self.chunk_x * self.size, world_y - self.chunk_y * self.size
