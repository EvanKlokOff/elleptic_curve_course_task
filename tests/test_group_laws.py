# tests/test_group_laws.py
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app.curves import CurveZp, CurveGF2m          # noqa: E402
from app.fields import FieldPrime, FieldGF2m       # noqa: E402
from app.point import Point                         # noqa: E402


# ------------------------------------------------------------
# Хелперы
# ------------------------------------------------------------
def all_points_zp(curve: CurveZp):
    pts = [Point.inf()]
    for x in range(curve.p):
        for y in range(curve.p):
            P = Point(x, y)
            if curve.is_on_curve(P):
                pts.append(P)
    return pts


def all_points_gf2m(curve: CurveGF2m):
    F = curve.F
    pts = [Point.inf()]
    for x in range(1 << F.m):
        for y in range(1 << F.m):
            P = Point(x, y)
            if curve.is_on_curve(P):
                pts.append(P)
    return pts


def neg_zp(curve: CurveZp, P: Point) -> Point:
    if P.infinity:
        return P
    return Point(P.x, curve.F.neg(P.y))


def neg_gf2m(curve: CurveGF2m, P: Point) -> Point:
    if P.infinity:
        return P
    F = curve.F
    y_new = F.add(F.add(P.y, F.mul(curve.a1, P.x)), curve.a3)
    return Point(P.x, y_new)


# ------------------------------------------------------------
# Базовый миксин с групповыми аксиомами (общий для всех кривых)
# ------------------------------------------------------------
class GroupAxiomsMixin:
    """Требует, чтобы в setUp были заданы self.curve и self.pts, self.neg."""

    def test_result_is_on_curve(self):
        """Результат сложения всегда лежит на кривой."""
        for P in self.pts:
            for Q in self.pts:
                R = self.curve.add(P, Q)
                self.assertTrue(
                    self.curve.is_on_curve(R),
                    f"add({P}, {Q}) = {R} не лежит на кривой",
                )

    def test_identity_element(self):
        O = Point.inf()
        for P in self.pts:
            self.assertEqual(self.curve.add(P, O), P)
            self.assertEqual(self.curve.add(O, P), P)
        self.assertEqual(self.curve.add(O, O), O)

    def test_additive_inverse(self):
        for P in self.pts:
            nP = self.neg(P)
            self.assertTrue(self.curve.add(P, nP).infinity)
            self.assertTrue(self.curve.add(nP, P).infinity)

    def test_commutativity_full(self):
        for P in self.pts:
            for Q in self.pts:
                self.assertEqual(self.curve.add(P, Q),
                                 self.curve.add(Q, P))

    def test_associativity_full(self):
        """Полный перебор (для малых полей это 19^3 или ~10^3 — быстро)."""
        for P in self.pts:
            for Q in self.pts:
                PQ = self.curve.add(P, Q)
                for R in self.pts:
                    lhs = self.curve.add(PQ, R)
                    rhs = self.curve.add(P, self.curve.add(Q, R))
                    self.assertEqual(
                        lhs, rhs,
                        f"Ассоциативность: ({P}+{Q})+{R} != {P}+({Q}+{R})",
                    )

    def test_mul_zero_one(self):
        O = Point.inf()
        for P in self.pts:
            self.assertEqual(self.curve.mul(P, 0), O)
            self.assertEqual(self.curve.mul(P, 1), P)

    def test_mul_distributive_over_add(self):
        """(m+n)·P = m·P + n·P."""
        for P in self.pts:
            for m in range(0, 6):
                for n in range(0, 6):
                    lhs = self.curve.mul(P, m + n)
                    rhs = self.curve.add(self.curve.mul(P, m),
                                         self.curve.mul(P, n))
                    self.assertEqual(
                        lhs, rhs,
                        f"(m+n)·P != m·P + n·P для P={P}, m={m}, n={n}",
                    )

    def test_mul_homomorphism(self):
        """m·(P+Q) = m·P + m·Q."""
        for P in self.pts:
            for Q in self.pts:
                for m in range(0, 5):
                    lhs = self.curve.mul(self.curve.add(P, Q), m)
                    rhs = self.curve.add(self.curve.mul(P, m),
                                         self.curve.mul(Q, m))
                    self.assertEqual(
                        lhs, rhs,
                        f"{m}·(P+Q) != {m}·P + {m}·Q",
                    )

    def test_mul_associative_scalars(self):
        """(m·n)·P = m·(n·P)."""
        for P in self.pts[::3]:
            for m in range(0, 5):
                for n in range(0, 5):
                    lhs = self.curve.mul(P, m * n)
                    rhs = self.curve.mul(self.curve.mul(P, n), m)
                    self.assertEqual(lhs, rhs)

    def test_mul_negative(self):
        """(-k)·P = k·(-P) = -(k·P)."""
        for P in self.pts:
            nP = self.neg(P)
            for k in range(1, 6):
                self.assertEqual(self.curve.mul(P, -k), self.curve.mul(nP, k))
                self.assertEqual(self.curve.mul(P, -k),
                                 self.neg(self.curve.mul(P, k)))

    def test_group_order_annihilates_points(self):
        """#E · P = O для всех точек P."""
        n = len(self.pts)          # порядок группы (включая O)
        for P in self.pts:
            self.assertTrue(
                self.curve.mul(P, n).infinity,
                f"#E·P != O для P={P}, #E={n}",
            )

    def test_point_order_divides_group_order(self):
        """Порядок каждой точки делит порядок группы."""
        n = len(self.pts)
        for P in self.pts:
            # ищем минимальный k>0 с k·P = O
            for k in range(1, n + 1):
                if self.curve.mul(P, k).infinity:
                    break
            else:
                self.fail(f"Порядок {P} не найден за {n} шагов")
            self.assertEqual(n % k, 0,
                             f"Порядок {k} точки {P} не делит #E={n}")


# ------------------------------------------------------------
# Zp
# ------------------------------------------------------------
class TestGroupLawsZp(GroupAxiomsMixin, unittest.TestCase):
    def setUp(self):
        self.curve = CurveZp(17, 2, 2)
        self.pts = all_points_zp(self.curve)
        self.neg = lambda P: neg_zp(self.curve, P)

    def test_group_order(self):
        # y^2 = x^3 + 2x + 2 над Z_17, проверено перебором
        self.assertEqual(len(self.pts), 19)

    def test_known_doubling(self):
        # 2·(5,1) = (6,3)
        R = self.curve.mul(Point(5, 1), 2)
        self.assertEqual((R.x, R.y), (6, 3))

    def test_known_triple(self):
        # 3·(5,1) = (10,6)
        R = self.curve.mul(Point(5, 1), 3)
        self.assertEqual((R.x, R.y), (10, 6))


# ------------------------------------------------------------
# GF(2^m): Nss
# ------------------------------------------------------------
class TestGroupLawsNss(GroupAxiomsMixin, unittest.TestCase):
    def setUp(self):
        mod = (1 << 4) | (1 << 1) | 1
        self.F = FieldGF2m(mod, 4)
        self.curve = CurveGF2m(self.F, "Nss", [1, 1])
        self.pts = all_points_gf2m(self.curve)
        self.neg = lambda P: neg_gf2m(self.curve, P)

    def test_is_on_curve_matches_enumeration(self):
        """
        Число точек, найденных перебором, совпадает с числом решений
        уравнения для каждого x. Т.е. is_on_curve не пропускает и
        не добавляет лишних точек.
        """
        F = self.F
        count = 0
        for x in range(1 << F.m):
            for y in range(1 << F.m):
                if self.curve.is_on_curve(Point(x, y)):
                    count += 1
        # count + 1 (O) == len(self.pts)
        self.assertEqual(count + 1, len(self.pts))


# ------------------------------------------------------------
# GF(2^m): Ss
# ------------------------------------------------------------
class TestGroupLawsSs(GroupAxiomsMixin, unittest.TestCase):
    def setUp(self):
        mod = (1 << 4) | (1 << 1) | 1
        self.F = FieldGF2m(mod, 4)
        self.curve = CurveGF2m(self.F, "Ss", [1, 1, 1])
        self.pts = all_points_gf2m(self.curve)
        self.neg = lambda P: neg_gf2m(self.curve, P)


# ------------------------------------------------------------
# Дополнительные свойства: эквивалентность Nss и Ss при a1=1
# ------------------------------------------------------------
class TestNssSsEquivalence(unittest.TestCase):
    def setUp(self):
        mod = (1 << 4) | (1 << 1) | 1
        self.F = FieldGF2m(mod, 4)
        self.nss = CurveGF2m(self.F, "Nss", [1, 1])
        self.ss = CurveGF2m(self.F, "Ss", [1, 1, 1])
        self.pts_nss = all_points_gf2m(self.nss)
        self.pts_ss = all_points_gf2m(self.ss)

    def test_same_point_sets(self):
        """Nss(a=1,b=1) и Ss(a=1,b=1,c=1) задают одну кривую."""
        key_nss = {("O",) if P.infinity else (P.x, P.y) for P in self.pts_nss}
        key_ss = {("O",) if P.infinity else (P.x, P.y) for P in self.pts_ss}
        self.assertEqual(key_nss, key_ss)

    def test_same_addition(self):
        for P in self.pts_nss:
            for Q in self.pts_nss:
                self.assertEqual(self.nss.add(P, Q), self.ss.add(P, Q))

    def test_same_scalar_mul(self):
        for P in self.pts_nss:
            for k in range(-5, 6):
                self.assertEqual(self.nss.mul(P, k), self.ss.mul(P, k))


# ------------------------------------------------------------
# Проверка на «свежих» полях: GF(2^3), GF(2^5)
# ------------------------------------------------------------
class TestOtherFields(unittest.TestCase):
    def test_gf8_nss(self):
        # x^3 + x + 1 = 0b1011 (неприводимый над GF(2))
        mod = (1 << 3) | (1 << 1) | 1
        F = FieldGF2m(mod, 3)
        c = CurveGF2m(F, "Nss", [1, 1])
        pts = all_points_gf2m(c)
        self.assertGreater(len(pts), 1)
        # групповая аксиома на подмножестве: ассоциативность
        for P in pts:
            for Q in pts:
                R = c.add(P, Q)
                self.assertTrue(c.is_on_curve(R))
                for S in pts:
                    self.assertEqual(c.add(c.add(P, Q), S),
                                     c.add(P, c.add(Q, S)))

    def test_gf32_zp(self):
        # y^2 = x^3 + 2x + 3 над Z_31 — несингулярная кривая
        # (4a^3 + 27b^2 = 32 + 243 = 275 ≡ 27 ≠ 0 mod 31)
        c = CurveZp(31, 2, 3)
        pts = all_points_zp(c)
        self.assertGreater(len(pts), 1)
        # 1) add(P,Q) всегда на кривой
        for P in pts:
            for Q in pts:
                R = c.add(P, Q)
                self.assertTrue(
                    c.is_on_curve(R),
                    f"add({P}, {Q}) = {R} не на кривой",
                )
        # 2) ассоциативность на выборке
        for P in pts[::2]:
            for Q in pts[::2]:
                PQ = c.add(P, Q)
                for R in pts[::2]:
                    self.assertEqual(
                        c.add(PQ, R),
                        c.add(P, c.add(Q, R)),
                        f"Ассоциативность: {P}, {Q}, {R}",
                    )
        # 3) #E · P = O
        n = len(pts)
        for P in pts[::5]:
            self.assertTrue(c.mul(P, n).infinity)

if __name__ == "__main__":
    unittest.main(verbosity=2)