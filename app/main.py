#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Арифметика эллиптических кривых над Zp и GF(2^m).

Типы кривых:
  Zp  - y^2 = x^3 + a*x + b  над Z_p
  Nss - y^2 + x*y = x^3 + a*x^2 + b  над GF(2^m)  (несуперсингулярная)
  Ss  - y^2 + a*x*y = x^3 + b*x^2 + c  над GF(2^m) (суперсингулярная)

Режимы запуска:
  python -m app.main <task.txt>              # один файл
  python -m app.main --in-dir IN --out-dir OUT
  python -m app.main -i IN -o OUT -f dec     # координаты в ответах — decimal
"""
import argparse
import sys
import os

# Позволяет запускать `python app/main.py ...` из корня проекта
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from app.curves import CurveZp, CurveGF2m
from app.fields import FieldGF2m
from app.parser import parse_modulus_line, tokenize_task_line
from app.utils import parse_int, parse_line_ints, set_output_base


# ============================================================
# Основная логика
# ============================================================
def solve_task_file(in_path: str, out_path: str):
    with open(in_path, "r", encoding="utf-8") as f:
        raw = [line.rstrip("\n") for line in f]
    # убираем пустые строки в конце
    while raw and not raw[-1].strip():
        raw.pop()

    if len(raw) < 3:
        raise ValueError("Файл задания слишком короткий")

    curve_type = raw[0].strip()
    field_line = raw[1].strip()
    curve_line = raw[2].strip()
    task_lines = raw[3:]

    if curve_type not in ("Zp", "Nss", "Ss"):
        raise ValueError(f"Неизвестный тип кривой: {curve_type}")

    # --- Поле и кривая ---
    if curve_type == "Zp":
        p = parse_int(field_line)
        coeffs = parse_line_ints(curve_line)
        if len(coeffs) != 2:
            raise ValueError("Для Zp нужны 2 коэффициента a b")
        curve = CurveZp(p, coeffs[0], coeffs[1])
    else:
        modulus = parse_modulus_line(field_line)
        m = modulus.bit_length() - 1
        F = FieldGF2m(modulus, m)
        coeffs = parse_line_ints(curve_line)
        if curve_type == "Nss":
            if len(coeffs) != 2:
                raise ValueError("Для Nss нужны 2 коэффициента a b")
        else:
            if len(coeffs) != 3:
                raise ValueError("Для Ss нужны 3 коэффициента a b c")
        curve = CurveGF2m(F, curve_type, coeffs)

    # --- Решение задач ---
    out_lines = []
    for line in task_lines:
        if not line.strip():
            continue
        parsed = tokenize_task_line(line)
        if parsed is None:
            continue
        op = parsed[0]
        if op == "A":
            _, P, Q = parsed
            if not curve.is_on_curve(P):
                out_lines.append(f"# Warning: {P} не лежит на кривой")
            if not curve.is_on_curve(Q):
                out_lines.append(f"# Warning: {Q} не лежит на кривой")
            R = curve.add(P, Q)
            out_lines.append(str(R))
        else:  # 'M'
            _, P, k = parsed
            if not curve.is_on_curve(P):
                out_lines.append(f"# Warning: {P} не лежит на кривой")
            R = curve.mul(P, k)
            out_lines.append(str(R))

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(out_lines) + ("\n" if out_lines else ""))


def _out_name_for(in_path: str, out_dir: str | None) -> str:
    if out_dir is None:
        base, ext = os.path.splitext(in_path)
        return base + "out" + ext
    os.makedirs(out_dir, exist_ok=True)
    return os.path.join(out_dir, os.path.basename(in_path))


def process_one(in_path: str, out_dir: str | None) -> str:
    out_path = _out_name_for(in_path, out_dir)
    solve_task_file(in_path, out_path)
    return out_path


def process_dir(in_dir: str, out_dir: str | None) -> list[str]:
    if not os.path.isdir(in_dir):
        raise NotADirectoryError(in_dir)
    if out_dir is None:
        out_dir = in_dir
    os.makedirs(out_dir, exist_ok=True)

    results = []
    for name in sorted(os.listdir(in_dir)):
        if not name.lower().endswith(".txt"):
            continue
        if name.endswith("out.txt"):
            continue
        in_path = os.path.join(in_dir, name)
        if not os.path.isfile(in_path):
            continue
        results.append(process_one(in_path, out_dir))
    return results


def _build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="curves",
        description="Арифметика эллиптических кривых над Zp и GF(2^m).",
    )
    p.add_argument("task_file", nargs="?",
                   help="Один .txt файл задания (взаимоисключим с --in-dir).")
    p.add_argument("-i", "--in-dir",
                   help="Папка с .txt заданиями (обрабатываются все файлы).")
    p.add_argument("-o", "--out-dir",
                   help="Папка для ответов (по умолчанию — рядом с заданиями).")
    p.add_argument("-f", "--format", choices=("hex", "dec"), default="hex",
                   help="Формат координат точек ТОЛЬКО в файлах ответов: "
                        "hex (по умолчанию) или dec. На вход не влияет.")
    return p


def main(argv: list[str]) -> int:
    parser = _build_argparser()
    args = parser.parse_args(argv[1:])

    # Влияет ТОЛЬКО на Point.__str__ при записи ответов.
    # Входной парсер parse_int от этого не зависит.
    set_output_base(16 if args.format == "hex" else 10)

    try:
        if args.task_file and args.in_dir:
            parser.error("Укажите либо <task_file>, либо --in-dir, но не оба")
        if not args.task_file and not args.in_dir:
            parser.error("Укажите <task_file> или --in-dir")

        if args.task_file:
            out_path = process_one(args.task_file, args.out_dir)
            print(f"Готово: {out_path}")
        else:
            written = process_dir(args.in_dir, args.out_dir)
            if not written:
                print("Нет .txt файлов для обработки.")
            else:
                print(f"Готово: {len(written)} файл(ов) обработано.")
                for pth in written:
                    print(f"  → {pth}")
    except (ValueError, NotADirectoryError, FileNotFoundError) as e:
        print(f"Ошибка: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))


