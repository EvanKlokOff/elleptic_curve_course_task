from app.fields import FieldPrime, FieldGF2m
from app.point import Point


# ============================================================
# Кривая над Zp:  y^2 = x^3 + a*x + b
# ============================================================


class CurveZp:
    def __init__(self, p: int, a: int, b: int):
        self.F = FieldPrime(p)
        self.a = a % p
        self.b = b % p
        self.p = p
        # проверка несингулярности: 4a³ + 27b² ≠ 0 (mod p)
        disc = (4 * self.a ** 3 + 27 * self.b ** 2) % p
        if disc == 0:
            raise ValueError(
                f"Сингулярная кривая: 4a³ + 27b² ≡ 0 (mod {p})"
            )


    def is_on_curve(self, P: Point) -> bool:
        if P.infinity:
            return True
        F = self.F
        lhs = F.mul(P.y, P.y)
        rhs = F.add(F.add(F.mul(F.mul(P.x, P.x), P.x),
                          F.mul(self.a, P.x)), self.b)
        return lhs == rhs

    def add(self, P: Point, Q: Point) -> Point:
        F = self.F
        if P.infinity: return Q
        if Q.infinity: return P

        if F.eq(P.x, Q.x):
            if F.eq(F.add(P.y, Q.y), 0):
                return Point.inf()
            # удвоение
            num = F.add(F.mul(3, F.mul(P.x, P.x)), self.a)
            den = F.mul(2, P.y)
            lam = F.div(num, den)
        else:
            num = F.sub(Q.y, P.y)
            den = F.sub(Q.x, P.x)
            lam = F.div(num, den)

        x3 = F.sub(F.sub(F.mul(lam, lam), P.x), Q.x)
        y3 = F.sub(F.mul(lam, F.sub(P.x, x3)), P.y)
        return Point(x3, y3)

    def mul(self, P: Point, k: int) -> Point:
        if k < 0:
            P = Point(P.x, self.F.neg(P.y), P.infinity)
            k = -k
        R = Point.inf()
        Q = P
        while k > 0:
            if k & 1:
                R = self.add(R, Q)
            Q = self.add(Q, Q)
            k >>= 1
        return R


# ============================================================
# Кривая над GF(2^m)
# ============================================================
class CurveGF2m:
    """
    Nss (несуперсингулярная): y^2 + x*y = x^3 + a*x^2 + b
        (т.е. a1=1, a3=1, a2=a, a4=0, a6=b)
    Ss (суперсингулярная):     y^2 + a*x*y = x^3 + b*x^2 + c
        (т.е. a1=a, a3=0, a2=b, a4=0, a6=c)
    """
    def __init__(self, F: FieldGF2m, kind: str, coeffs):
        self.F = F
        self.kind = kind
        if kind == "Nss":
            self.a1, self.a3 = 1, 0
            self.a2, self.a4 = coeffs[0], 0
            self.a6 = coeffs[1]
        else:  # Ss
            self.a1 = coeffs[0]
            self.a3 = 0
            self.a2 = coeffs[1]
            self.a4 = 0
            self.a6 = coeffs[2]
        if self.a6 == 0:
            raise ValueError("Сингулярная кривая: a6 = 0")

    def is_on_curve(self, P: Point) -> bool:
        if P.infinity:
            return True
        F = self.F
        # y^2 + a1*x*y + a3*y = x^3 + a2*x^2 + a4*x + a6
        lhs = F.add(
            F.add(F.mul(P.y, P.y), F.mul(self.a1, F.mul(P.x, P.y))),
            F.mul(self.a3, P.y)
        )
        rhs = F.add(
            F.add(
                F.add(F.mul(F.mul(P.x, P.x), P.x),
                      F.mul(self.a2, F.mul(P.x, P.x))),
                F.mul(self.a4, P.x)
            ), self.a6
        )
        return F.eq(lhs, rhs)

    def add(self, P: Point, Q: Point) -> Point:
        F = self.F
        if P.infinity: return Q
        if Q.infinity: return P

        if F.eq(P.x, Q.x):
            if F.eq(F.add(F.add(P.y, Q.y),
                          F.add(F.mul(self.a1, P.x), self.a3)), 0):
                return Point.inf()
            den = F.add(F.mul(self.a1, P.x), self.a3)
            if den == 0:
                return Point.inf()
            num = F.add(F.add(F.mul(P.x, P.x), self.a4),
                        F.mul(self.a1, P.y))
            lam = F.div(num, den)
        else:
            lam = F.div(F.add(P.y, Q.y), F.add(P.x, Q.x))

        x3 = F.add(F.add(F.add(F.mul(lam, lam),
                               F.mul(self.a1, lam)), self.a2),
                   F.add(P.x, Q.x))
        y3 = F.add(F.add(F.mul(lam, F.add(P.x, x3)), x3), P.y)  # ← +x3!
        return Point(x3, y3)

    def mul(self, P: Point, k: int) -> Point:
        if k < 0:
            # -P = (x, y + a1*x + a3)
            negP = Point(P.x, self.F.add(self.F.add(P.y, self.F.mul(self.a1, P.x)),
                                         self.a3), P.infinity)
            P = negP
            k = -k
        R = Point.inf()
        Q = P
        while k > 0:
            if k & 1:
                R = self.add(R, Q)
            Q = self.add(Q, Q)
            k >>= 1
        return R
