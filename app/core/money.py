from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP


TWOPLACES = Decimal("0.01")


def money_round(value) -> float:
    return float(Decimal(str(value)).quantize(TWOPLACES, rounding=ROUND_HALF_UP))
