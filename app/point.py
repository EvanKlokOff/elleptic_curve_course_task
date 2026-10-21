# ============================================================
# Точка
# ============================================================
from dataclasses import dataclass

from app.utils import format_int


@dataclass
class Point:
    x: int
    y: int
    infinity: bool = False

    @staticmethod
    def inf():
        return Point(0, 0, True)

    def __str__(self):
        if self.infinity:
            return "O"
        return f"({format_int(self.x)}, {format_int(self.y)})"