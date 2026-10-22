# tools/generate_gf2m_tasks.py
import sys
import os

# Три dirname: app/tools/ → app/ → корень проекта
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from app.curves import CurveGF2m      # noqa: E402
from app.fields import FieldGF2m      # noqa: E402
from app.point import Point           # noqa: E402


# Параметры Koblitz-кривых (Nss).
# Для 233/283/409/571 Gx, Gy НЕ приведены — их нужно взять из SEC 2.
CURVES_K = {
    "k163": {
        "m": 163,
        # f(x) = x^163 + x^7 + x^6 + x^3 + 1 → маска из степеней
        "poly_powers": [163, 7, 6, 3, 0],
        "a": 1,
        "b": 1,
        "Gx": 0x02fe13c0537bbc11acaa07d793de4e6d5e5c94eee8,
        "Gy": 0x0289070fb05d38ff58321f2e800536d538ccdaa3d9,
    },
    "k233": {
        "m": 233,
        # f(x) = x^233 + x^74 + 1
        "poly_powers": [233, 74, 0],
        "a": 0,
        "b": 1,
        "Gx": 0x017232ba853a7e731af129f22ff4149563a419c26bf50a4c9d6eefad6126,
        "Gy": 0x01db537dece819b7f70f555a67c427a8cd9bf18aeb9b56e0c11056fae6a3,
    },
    "k283": {
        "m": 283,
        # f(x) = x^283 + x^12 + x^7 + x^5 + 1
        "poly_powers": [283, 12, 7, 5, 0],
        "a": 0,
        "b": 1,
        "Gx": 0x503213f78ca44883f1a3b8162f188e553cd265f23c1567a16876913b0c2ac2458492836,
        "Gy": 0x1ccda380f1c9e318d90f95d07e5426fe87e45c0e8184698e45962364e34116177dd2259,
    },
    "k409": {
        "m": 409,
        # f(x) = x^409 + x^87 + 1
        "poly_powers": [409, 87, 0],
        "a": 0, "b": 1,
        "Gx": 0x060f05f658f49c1ad3ab1890f7184210efd0987e307c84c27accfb8f9f67cc2c460189eb5aaaa62ee222eb1b35540cfe9023746,
        "Gy": 0x1e369050b7c4e42acba1dacbf04299c3460782f918ea427e6325165e9ea10e3da5f6c42e9c55215aa9ca27a5863ec48d8e0286b,   # ← sect409k1
    },
    "k571": {
        "m": 571,
        # f(x) = x^571 + x^10 + x^5  + x^2 + 1
        "poly_powers": [571, 10, 5, 2, 0],
        "a": 0, "b": 1,
        "Gx": 0x26eb7a859923fbc82189631f8103fe4ac9ca2970012d5d46024804801841ca44370958493b205e647da304db4ceb08cbbd1ba39494776fb988b47174dca88c7e2945283a01c8972,
        "Gy": 0x349dc807f4fbf374f4aeade3bca95314dd58cec9f307a54ffc61efc006d8a2c9d4979c0ac44aea74fbebbb9f772aedcb620b01a7ba7af1b320430c8591984f601cd4c143ef1c7a3,   # ← sect571k1
    },
}


def _build_modulus(poly_powers: list[int]) -> int:
    """Собирает многочлен-модуль из списка степеней в целое (битовая маска)."""
    mod = 0
    for d in poly_powers:
        mod |= (1 << d)
    return mod


def gen_gf2m_task(name: str, params: dict, out_dir: str = "IN") -> None:
    m = params["m"]
    mod = _build_modulus(params["poly_powers"])
    F = FieldGF2m(mod, m)

    c = CurveGF2m(F, "Nss", [params["a"], params["b"]])
    G = Point(params["Gx"], params["Gy"])

    if not c.is_on_curve(G):
        raise ValueError(f"{name}: G не лежит на кривой!")

    # Строка поля: (163 7 6 3 0) и т.д.
    poly_line = "(" + " ".join(str(d) for d in params["poly_powers"]) + ")"
    lines = ["Nss", poly_line, f"{params['a']} {params['b']}"]

    # 5 задач сложения: G + kG, k = 2..6
    for k in range(2, 7):
        kG = c.mul(G, k)
        lines.append(
            f"A ({hex(G.x)} {hex(G.y)}) ({hex(kG.x)} {hex(kG.y)})"
        )

    # 5 задач умножения: kG, k = 2, 3, 5, 10, 100
    for k in [2, 3, 5, 10, 100]:
        kG = c.mul(G, k)
        lines.append(f"M ({hex(G.x)} {hex(G.y)}) {k}")

    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{name}_task.txt")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"✅ {out_path}: 10 задач")


if __name__ == "__main__":
    for name, params in CURVES_K.items():
        gen_gf2m_task(name, params)