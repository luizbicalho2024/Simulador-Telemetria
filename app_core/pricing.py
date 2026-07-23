from __future__ import annotations

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any

MONEY_QUANT = Decimal("0.01")
PERCENT_QUANT = Decimal("0.01")


def to_decimal(value: Any, fallback: Decimal | str = Decimal("0")) -> Decimal:
    """Converte valores numéricos para Decimal sem propagar NaN ou infinito."""
    fallback_decimal = fallback if isinstance(fallback, Decimal) else Decimal(str(fallback))
    try:
        result = value if isinstance(value, Decimal) else Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return fallback_decimal
    return result if result.is_finite() else fallback_decimal


def quantize_money(value: Any) -> Decimal:
    return to_decimal(value).quantize(MONEY_QUANT, rounding=ROUND_HALF_UP)


def quantize_percent(value: Any) -> Decimal:
    return to_decimal(value).quantize(PERCENT_QUANT, rounding=ROUND_HALF_UP)


def gross_margin_value(sale_price: Any, cost: Any) -> Decimal:
    """Margem bruta unitária: preço de venda menos custo."""
    return quantize_money(to_decimal(sale_price) - to_decimal(cost))


def gross_margin_percent(sale_price: Any, cost: Any) -> Decimal | None:
    """Margem bruta como percentual do preço de venda.

    Fórmula: (preço - custo) / preço * 100.
    Retorna ``None`` quando o preço de venda é zero.
    """
    sale = to_decimal(sale_price)
    if sale == 0:
        return None
    margin = ((sale - to_decimal(cost)) / sale) * Decimal("100")
    return quantize_percent(margin)


def sale_price_from_margin(cost: Any, target_margin_percent: Any) -> Decimal:
    """Calcula o preço necessário para atingir uma margem bruta alvo.

    A margem é calculada sobre o preço de venda. Portanto:
    preço = custo / (1 - margem/100).
    """
    normalized_cost = to_decimal(cost)
    target = to_decimal(target_margin_percent)
    if normalized_cost < 0:
        raise ValueError("O custo não pode ser negativo.")
    if target < 0 or target >= 100:
        raise ValueError("A margem personalizada deve estar entre 0% e 99,99%.")
    denominator = Decimal("1") - (target / Decimal("100"))
    return quantize_money(normalized_cost / denominator)


def margin_summary(sale_price: Any, cost: Any) -> dict[str, Decimal | None]:
    sale = quantize_money(sale_price)
    normalized_cost = quantize_money(cost)
    return {
        "sale_price": sale,
        "cost": normalized_cost,
        "margin_value": gross_margin_value(sale, normalized_cost),
        "margin_percent": gross_margin_percent(sale, normalized_cost),
    }
