# ============================================================
# Парсинг файла задания
# ============================================================
from app.point import Point
from app.utils import parse_int, parse_line_ints


def parse_modulus_line(line: str) -> int:
    """
    '(...)' — список степеней одночленов (4 1 0) -> x^4 + x + 1 = 0b10011
    либо одиночное число (на случай если решено задавать иначе).
    """
    s = line.strip()
    if s.startswith("(") and s.endswith(")"):
        inside = s[1:-1].strip()
        if not inside:
            raise ValueError("Пустой модуль")
        # степени могут быть в десятичной системе
        powers = parse_line_ints(inside)
        poly = 0
        for d in powers:
            poly |= (1 << d)
        return poly
    else:
        # просто число (не рекомендуется, но допустим)
        return parse_int(s)


def parse_point_token(tok: str) -> Point:
    """
    Точка задаётся как '(x y)' или '(x,y)' — в строке могут быть пробелы.
    Токены уже разбиты по пробелам... => обрабатываем цепочку.
    """
    s = tok.strip()
    # Ожидаем вид: (x y) или (x,y)
    s = s.strip()
    if s.startswith("(") and s.endswith(")"):
        s = s[1:-1]
    parts = s.replace(",", " ").split()
    if len(parts) != 2:
        raise ValueError(f"Некорректная точка: {tok}")
    return Point(parse_int(parts[0]), parse_int(parts[1]))


def tokenize_task_line(line: str):
    """
    Разбирает строку задачи:  'A (x1 y1) (x2 y2)'   или   'M (x y) k'.
    Возвращает ('A', Point, Point) или ('M', Point, int).
    """
    # разобьём, но склеивая содержимое скобок
    tokens = []
    buf = ""
    depth = 0
    for ch in line:
        if ch == '(':
            depth += 1
            buf += ch
        elif ch == ')':
            depth -= 1
            buf += ch
        elif ch.isspace() and depth == 0:
            if buf:
                tokens.append(buf)
                buf = ""
        else:
            buf += ch
    if buf:
        tokens.append(buf)

    if not tokens:
        return None
    op = tokens[0].upper()
    if op == "A":
        if len(tokens) != 3:
            raise ValueError(f"A ожидает 2 точки: {line}")
        P = parse_point_token(tokens[1])
        Q = parse_point_token(tokens[2])
        return ("A", P, Q)
    elif op == "M":
        if len(tokens) != 3:
            raise ValueError(f"M ожидает точку и число: {line}")
        P = parse_point_token(tokens[1])
        k = parse_int(tokens[2])
        return ("M", P, k)
    else:
        raise ValueError(f"Неизвестная операция: {op}")
