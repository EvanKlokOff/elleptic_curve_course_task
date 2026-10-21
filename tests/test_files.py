# tests/test_files.py
import os
import sys
import tempfile
import unittest

# добавляем корень проекта в sys.path
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app.main import solve_task_file  # noqa: E402


IN_DIR = os.path.join(ROOT, "IN")
OUT_DIR = os.path.join(ROOT, "OUT")


def _list_txt(folder):
    return sorted(
        f for f in os.listdir(folder)
        if f.endswith(".txt")
    ) if os.path.isdir(folder) else []


class TestFiles(unittest.TestCase):
    """Прогоняет каждый IN/*.txt и сравнивает с OUT/*.txt."""

    def test_all_files(self):
        in_files = _list_txt(IN_DIR)
        self.assertTrue(in_files, f"Нет .txt в {IN_DIR}")

        for name in in_files:
            with self.subTest(file=name):
                in_path = os.path.join(IN_DIR, name)
                ref_path = os.path.join(OUT_DIR, name)
                self.assertTrue(
                    os.path.isfile(ref_path),
                    f"Нет эталона {ref_path} для {name}",
                )

                with tempfile.TemporaryDirectory() as tmpdir:
                    out_path = os.path.join(tmpdir, "out.txt")
                    solve_task_file(in_path, out_path)

                    with open(out_path, "r", encoding="utf-8") as f:
                        got = f.read().splitlines()
                    with open(ref_path, "r", encoding="utf-8") as f:
                        expected = f.read().splitlines()

                self.assertEqual(
                    got, expected,
                    f"\nФайл {name}: результат не совпал.\n"
                    f"  получено: {got}\n"
                    f"  ожидалось: {expected}"
                )