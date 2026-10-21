# ============================================================
# Арифметика в GF(p)
# ============================================================
class FieldPrime:
    def __init__(self, p: int):
        assert p > 1
        self.p = p

    def add(self, a, b): return (a + b) % self.p
    def sub(self, a, b): return (a - b) % self.p
    def mul(self, a, b): return (a * b) % self.p

    def inv(self, a):
        a %= self.p
        if a == 0:
            raise ZeroDivisionError("Деление на 0 в Z_p")
        return pow(a, self.p - 2, self.p)

    def div(self, a, b): return self.mul(a, self.inv(b))
    def neg(self, a): return (-a) % self.p
    def zero(self): return 0
    def one(self): return 1

    def eq(self, a, b): return (a - b) % self.p == 0


# ============================================================
# Арифметика в GF(2^m) через полиномы
# ============================================================
class FieldGF2m:
    """
    Элемент поля — целое число (битовая маска многочлена над Z_2).
    Модуль — неприводимый многочлен, заданный как целое число,
    представляющее его биты.
    """

    def __init__(self, modulus_bits: int, m: int):
        self.m = m
        self.modulus = modulus_bits  # многочлен-модуль как целое
        self.mask = (1 << m) - 1

    # -- базовые операции над полиномами --
    def _deg(self, a: int) -> int:
        return a.bit_length() - 1 if a else -1

    def _poly_mod(self, a: int) -> int:
        """Приведение многочлена по модулю self.modulus."""
        deg_mod = self._deg(self.modulus)
        while a.bit_length() - 1 >= deg_mod and a:
            shift = (a.bit_length() - 1) - deg_mod
            a ^= self.modulus << shift
        return a & self.mask

    def add(self, a, b): return a ^ b          # сложение = XOR
    def sub(self, a, b): return a ^ b          # в GF(2^m) вычитание = сложение
    def neg(self, a): return a                 # -a = a

    def mul(self, a, b) -> int:
        r = 0
        while b:
            if b & 1:
                r ^= a
            b >>= 1
            a <<= 1
        return self._poly_mod(r)

    def _extended_gcd(self, a, b):
        """Расширенный алгоритм Евклида для полиномов над GF(2)."""
        old_r, r = a, b
        old_s, s = 1, 0
        old_t, t = 0, 1
        while r:
            # частное от деления old_r на r
            q = 0
            d_old = self._deg(old_r)
            d_r = self._deg(r)
            dividend = old_r
            while dividend and self._deg(dividend) >= d_r:
                shift = self._deg(dividend) - d_r
                q ^= (1 << shift)
                dividend ^= (r << shift)
            old_r, r = r, dividend
            old_s, s = s, old_s ^ self._mul_poly(s, q)
            old_t, t = t, old_t ^ self._mul_poly(t, q)
        return old_r, old_s, old_t

    def _mul_poly(self, a, b):
        """Умножение полиномов без приведения по модулю (для extended_gcd)."""
        r = 0
        while b:
            if b & 1:
                r ^= a
            b >>= 1
            a <<= 1
        return r

    def inv(self, a: int) -> int:
        if a == 0:
            raise ZeroDivisionError("Деление на 0 в GF(2^m)")
        g, s, _ = self._extended_gcd(a, self.modulus)
        # g должен быть константой 1 (НОД = 1)
        if g != 1:
            raise ZeroDivisionError("Элемент не обратим")
        return self._poly_mod(s)

    def div(self, a, b): return self.mul(a, self.inv(b))
    def zero(self): return 0
    def one(self): return 1
    def eq(self, a, b): return a == b
