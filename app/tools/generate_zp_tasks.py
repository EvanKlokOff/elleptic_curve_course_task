# tools/generate_zp_tasks.py
import sys
import os

# Позволяет запускать `python app/main.py ...` из корня проекта
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from app.curves import CurveZp
from app.point import Point


# Параметры NIST-кривых над Zp из открытых источников [citation:7]
CURVES_ZP = {
    "p192": {
        "p": 0xfffffffffffffffffffffffffffffffeffffffffffffffff,
        "b": 0x64210519e59c80e70fa7e9ab72243049feb8deecc146b9b1,
        "Gx": 0x188da80eb03090f67cbf20eb43a18800f4ff0afd82ff1012,
        "Gy": 0x07192b95ffc8da78631011ed6b24cdd573f977a11e794811,
    },
    "p224": {
        "p": 0xffffffffffffffffffffffffffffffff000000000000000000000001,
        "b": 0xb4050a850c04b3abf54132565044b0b7d7bfd8ba270b39432355ffb4,
        "Gx": 0xb70e0cbd6bb4bf7f321390b94a03c1d356c21122343280d6115c1d21,
        "Gy": 0xbd376388b5f723fb4c22dfe6cd4375a05a07476444d5819985007e34,
    },
    "p256": {
        "p": 0xffffffff00000001000000000000000000000000ffffffffffffffffffffffff,
        "b": 0x5ac635d8aa3a93e7b3ebbd55769886bc651d06b0cc53b0f63bce3c3e27d2604b,
        "Gx": 0x6b17d1f2e12c4247f8bce6e563a440f277037d812deb33a0f4a13945d898c296,
        "Gy": 0x4fe342e2fe1a7f9b8ee7eb4a7c0f9e162bce33576b315ececbb6406837bf51f5,
    },
    "p384": {
        "p": 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffeffffffff0000000000000000ffffffff,
        "b": 0xb3312fa7e23ee7e4988e056be3f82d19181d9c6efe8141120314088f5013875ac656398d8a2ed19d2a85c8edd3ec2aef,
        "Gx": 0xaa87ca22be8b05378eb1c71ef320ad746e1d3b628ba79b9859f741e082542a385502f25dbf55296c3a545e3872760ab7,
        "Gy": 0x3617de4a96262c6f5d9e98bf9292dc29f8f41dbd289a147ce9da3113b5f0b8c00a60b1ce1d7e819d7a431d7c90ea0e5f,
    },
    "p521": {
        "p": 0x01ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff,
        "b": 0x0051953eb9618e1c9a1f929a21a0b68540eea2da725b99b315f3b8b489918ef109e156193951ec7e937b1652c0bd3bb1bf073573df883d2c34f1ef451fd46b503f00,
        "Gx": 0x00c6858e06b70404e9cd9e3ecb662395b4429c648139053fb521f828af606b4d3dbaa14b5e77efe75928fe1dc127a2ffa8de3348b3c1856a429bf97e7e31c2e5bd66,
        "Gy": 0x011839296a789a3bc0045c8a5fb42c7d1bd998f54449579b446817afbd17273e662c97ee72995ef42640c550b9013fad0761353c7086a272c24088be94769fd16650,
    },
}

def gen_zp_task(name, params, out_dir="IN"):
    p, b = params["p"], params["b"]
    a = (p - 3) % p  # a = -3 для всех NIST Zp кривых
    c = CurveZp(p, a, b)
    G = Point(params["Gx"], params["Gy"])
    if not c.is_on_curve(G):
        raise ValueError(f"{name}: G не лежит на кривой!")

    lines = ["Zp", hex(p), f"{hex(a)} {hex(b)}"]

    # 5 задач сложения: G + kG для k = 2..6
    for k in range(2, 7):
        kG = c.mul(G, k)
        lines.append(f"A ({hex(G.x)} {hex(G.y)}) ({hex(kG.x)} {hex(kG.y)})")

    # 5 задач умножения: kG для k = 2,3,5,10,100
    for k in [2, 3, 5, 10, 100]:
        kG = c.mul(G, k)
        lines.append(f"M ({hex(G.x)} {hex(G.y)}) {k}")

    out_path = f"{out_dir}/{name}_task.txt"
    with open(out_path, "w") as f:
        f.write("\n".join(lines) + "\n")
    print(f"✅ {out_path}: 10 задач")

if __name__ == "__main__":
    for name, params in CURVES_ZP.items():
        gen_zp_task(name, params)