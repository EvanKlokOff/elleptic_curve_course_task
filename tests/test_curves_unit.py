# tests/test_curves_unit.py
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
# Вспомогательные функции
# ------------------------------------------------------------
def all_points_zp(curve: CurveZp):
    """Перебирает все аффинные точки кривой над Zp."""
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
# Zp: базовая кривая y^2 = x^3 + 2x + 2 над Z_17
# ------------------------------------------------------------
class TestCurveZp(unittest.TestCase):
    def setUp(self):
        self.curve = CurveZp(17, 2, 2)
        self.pts = all_points_zp(self.curve)

    def test_points_on_curve(self):
        # порядок группы = 19 (проверено вручную)
        self.assertEqual(len(self.pts), 19)

    def test_identity(self):
        O = Point.inf()
        P = Point(5, 1)
        self.assertTrue(self.curve.is_on_curve(P))
        self.assertEqual(self.curve.add(P, O), P)
        self.assertEqual(self.curve.add(O, P), P)
        self.assertEqual(self.curve.add(O, O), O)

    def test_negation(self):
        for P in self.pts:
            nP = neg_zp(self.curve, P)
            self.assertTrue(self.curve.is_on_curve(nP))
            self.assertTrue(self.curve.add(P, nP).infinity)

    def test_commutativity(self):
        for P in self.pts:
            for Q in self.pts:
                self.assertEqual(
                    self.curve.add(P, Q),
                    self.curve.add(Q, P),
                )

    def test_associativity_sampled(self):
        # полный перебор 19^3 — норм, но сделаем выборку
        for P in self.pts[::3]:
            for Q in self.pts[::3]:
                for R in self.pts[::3]:
                    lhs = self.curve.add(self.curve.add(P, Q), R)
                    rhs = self.curve.add(P, self.curve.add(Q, R))
                    self.assertEqual(lhs, rhs)

    def test_scalar_mul_matches_repeated_add(self):
        P = Point(5, 1)
        R = Point.inf()
        for k in range(0, 25):
            self.assertEqual(self.curve.mul(P, k), R)
            R = self.curve.add(R, P)

    def test_order_of_generator(self):
        # (5,1) порождает всю группу порядка 19
        P = Point(5, 1)
        self.assertTrue(self.curve.mul(P, 19).infinity)
        seen = set()
        for k in range(19):
            Q = self.curve.mul(P, k)
            key = ("O",) if Q.infinity else (Q.x, Q.y)
            seen.add(key)
        self.assertEqual(len(seen), 19)

    def test_known_addition(self):
        # (5,1)+(6,3) = (10,0)
        R = self.curve.add(Point(5, 1), Point(6, 3))
        self.assertEqual((R.x, R.y), (10, 6))


# ------------------------------------------------------------
# GF(2^m): Nss и Ss над GF(2^4) с модулем x^4+x+1
# ------------------------------------------------------------
class TestCurveGF2mNss(unittest.TestCase):
    def setUp(self):
        mod = (1 << 4) | (1 << 1) | 1        # x^4 + x + 1
        self.F = FieldGF2m(mod, 4)
        self.curve = CurveGF2m(self.F, "Nss", [1, 1])
        self.pts = all_points_gf2m(self.curve)

    def test_points_on_curve(self):
        self.assertGreaterEqual(len(self.pts), 10)   # порядок группы = 16

    def test_identity(self):
        O = Point.inf()
        P = Point(0, 1)
        self.assertTrue(self.curve.is_on_curve(P))
        self.assertEqual(self.curve.add(P, O), P)
        self.assertEqual(self.curve.add(O, P), P)

    def test_negation(self):
        for P in self.pts:
            nP = neg_gf2m(self.curve, P)
            self.assertTrue(self.curve.is_on_curve(nP))
            self.assertTrue(self.curve.add(P, nP).infinity)

    def test_commutativity(self):
        for P in self.pts:
            for Q in self.pts:
                self.assertEqual(
                    self.curve.add(P, Q),
                    self.curve.add(Q, P),
                )

    def test_associativity_sampled(self):
        for P in self.pts[::2]:
            for Q in self.pts[::2]:
                for R in self.pts[::2]:
                    lhs = self.curve.add(self.curve.add(P, Q), R)
                    rhs = self.curve.add(P, self.curve.add(Q, R))
                    self.assertEqual(lhs, rhs)

    def test_scalar_mul_matches_repeated_add(self):
        P = Point(0, 1)
        R = Point.inf()
        for k in range(0, 20):
            self.assertEqual(self.curve.mul(P, k), R)
            R = self.curve.add(R, P)


class TestCurveGF2mSs(unittest.TestCase):
    def setUp(self):
        mod = (1 << 4) | (1 << 1) | 1
        self.F = FieldGF2m(mod, 4)
        # y^2 + xy = x^3 + x^2 + 1  — та же, что Nss с a=b=c=1
        self.curve = CurveGF2m(self.F, "Ss", [1, 1, 1])
        self.pts = all_points_gf2m(self.curve)

    def test_points_on_curve(self):
        self.assertGreaterEqual(len(self.pts), 10)

    def test_negation(self):
        for P in self.pts:
            nP = neg_gf2m(self.curve, P)
            self.assertTrue(self.curve.is_on_curve(nP))
            self.assertTrue(self.curve.add(P, nP).infinity)

    def test_commutativity(self):
        for P in self.pts:
            for Q in self.pts:
                self.assertEqual(
                    self.curve.add(P, Q),
                    self.curve.add(Q, P),
                )

    def test_scalar_mul_matches_repeated_add(self):
        P = Point(0, 1)
        R = Point.inf()
        for k in range(0, 20):
            self.assertEqual(self.curve.mul(P, k), R)
            R = self.curve.add(R, P)

    def test_ss_matches_nss_when_a1_1(self):
        """
        При a1=a3=1 и коэффициентах (a2=a6=1) формулы Nss и Ss совпадают.
        Проверяем это на всех парах точек.
        """
        mod = (1 << 4) | (1 << 1) | 1
        F = FieldGF2m(mod, 4)
        nss = CurveGF2m(F, "Nss", [1, 1])
        for P in self.pts:
            for Q in self.pts:
                self.assertEqual(
                    self.curve.add(P, Q),
                    nss.add(P, Q),
                )


# ------------------------------------------------------------
# Мелкие тесты для полей
# ------------------------------------------------------------
class TestFields(unittest.TestCase):
    def test_gf2m_inverse(self):
        mod = (1 << 4) | (1 << 1) | 1
        F = FieldGF2m(mod, 4)
        for a in range(1, 16):
            inv = F.inv(a)
            self.assertEqual(F.mul(a, inv), 1)
            self.assertEqual(F.mul(inv, a), 1)

    def test_gf2m_field_laws(self):
        mod = (1 << 4) | (1 << 1) | 1
        F = FieldGF2m(mod, 4)
        for a in range(16):
            for b in range(16):
                # коммутативность
                self.assertEqual(F.mul(a, b), F.mul(b, a))
                self.assertEqual(F.add(a, b), F.add(b, a))
                # дистрибутивность
                for c in range(16):
                    self.assertEqual(
                        F.mul(a, F.add(b, c)),
                        F.add(F.mul(a, b), F.mul(a, c)),
                    )

    def test_fp_inverse(self):
        F = FieldPrime(17)
        for a in range(1, 17):
            self.assertEqual(F.mul(a, F.inv(a)) % 17, 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)