# ============================================================
# Парсинг чисел: поддержка 10 и 16-ричной системы
# ============================================================
def parse_int(token: str) -> int:
    """Парсит число. '0x..' или содержит [a-f] -> hex, иначе decimal."""
    t = token.strip()
    if t.lower().startswith("0x"):
        return int(t, 16)
    # Если есть буквы a-f (и это не десятичное) — считаем hex
    if any(ch in "abcdefABCDEF" for ch in t):
        return int(t, 16)
    return int(t, 10)


def parse_line_ints(line: str):
    """Разбивает строку по пробелам/запятым на int-ы."""
    tokens = line.replace(",", " ").split()
    return [parse_int(t) for t in tokens]


# ============================================================
# Форматирование выходных чисел
# (используется ТОЛЬКО при записи файлов ответов)
# ============================================================
_OUTPUT_BASE = 16  # по умолчанию hex


def set_output_base(base: int) -> None:
    """Устанавливает формат ВЫВОДА в файлы ответов: 10 или 16."""
    global _OUTPUT_BASE
    if base not in (10, 16):
        raise ValueError("Допустимые форматы вывода: 10 или 16")
    _OUTPUT_BASE = base


def get_output_base() -> int:
    return _OUTPUT_BASE


def format_int(v: int) -> str:
    """Формат координат в файле ответа (10 или 16, задаётся через -f)."""
    if _OUTPUT_BASE == 16:
        return hex(v)
    return str(v)