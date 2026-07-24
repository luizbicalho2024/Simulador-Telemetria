from __future__ import annotations

from decimal import Decimal, InvalidOperation, ROUND_CEILING, ROUND_HALF_UP
from typing import Any, Iterable

MONEY_QUANT = Decimal("0.01")
PERCENT_QUANT = Decimal("0.01")
MIN_CUSTOM_MARGIN_PERCENT = Decimal("30.00")


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
    """Margem bruta: preço de venda menos custo."""
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

    A margem é calculada sobre o preço de venda:
    preço = custo / (1 - margem/100).
    """
    normalized_cost = to_decimal(cost)
    target = to_decimal(target_margin_percent)
    if normalized_cost < 0:
        raise ValueError("O custo não pode ser negativo.")
    if target < MIN_CUSTOM_MARGIN_PERCENT or target >= 100:
        raise ValueError(
            f"A margem personalizada deve estar entre {MIN_CUSTOM_MARGIN_PERCENT:.2f}% e 99,99%."
        )
    denominator = Decimal("1") - (target / Decimal("100"))
    return quantize_money(normalized_cost / denominator)


def minimum_sale_price(cost: Any, minimum_margin_percent: Any = MIN_CUSTOM_MARGIN_PERCENT) -> Decimal:
    """Preço mínimo permitido para preservar a margem configurada."""
    return sale_price_from_margin(cost, minimum_margin_percent)


def margin_summary(sale_price: Any, cost: Any) -> dict[str, Decimal | None]:
    sale = quantize_money(sale_price)
    normalized_cost = quantize_money(cost)
    return {
        "sale_price": sale,
        "cost": normalized_cost,
        "margin_value": gross_margin_value(sale, normalized_cost),
        "margin_percent": gross_margin_percent(sale, normalized_cost),
    }


def validate_minimum_margin(
    sale_price: Any,
    cost: Any,
    minimum_margin_percent: Any = MIN_CUSTOM_MARGIN_PERCENT,
) -> tuple[bool, Decimal | None]:
    """Valida se o preço respeita o piso de margem."""
    percent = gross_margin_percent(sale_price, cost)
    minimum = quantize_percent(minimum_margin_percent)
    return bool(percent is not None and percent >= minimum), percent


def proposal_totals(
    *,
    recurring_sale_per_vehicle: Any,
    recurring_cost_per_vehicle: Any,
    months: Any,
    vehicles: Any,
    installation_sale_per_vehicle: Any = 0,
    installation_cost_per_vehicle: Any = 0,
    charge_installation: bool = True,
    fixed_cost: Any = 0,
) -> dict[str, Decimal | None]:
    """Consolida receita, custo e margem de uma proposta PJ.

    A instalação é receita apenas quando cobrada, mas seu custo sempre é
    considerado. O custo fixo é aplicado uma vez por proposta.
    """
    vehicle_count = max(Decimal("1"), to_decimal(vehicles, "1"))
    contract_months = max(Decimal("1"), to_decimal(months, "1"))

    monthly_sale_vehicle = quantize_money(recurring_sale_per_vehicle)
    monthly_cost_vehicle = quantize_money(recurring_cost_per_vehicle)
    installation_sale_vehicle = quantize_money(installation_sale_per_vehicle)
    installation_cost_vehicle = quantize_money(installation_cost_per_vehicle)
    normalized_fixed_cost = quantize_money(fixed_cost)

    recurring_revenue = quantize_money(monthly_sale_vehicle * contract_months * vehicle_count)
    recurring_cost = quantize_money(monthly_cost_vehicle * contract_months * vehicle_count)
    installation_revenue = (
        quantize_money(installation_sale_vehicle * vehicle_count)
        if charge_installation
        else Decimal("0.00")
    )
    installation_cost = quantize_money(installation_cost_vehicle * vehicle_count)

    total_revenue = quantize_money(recurring_revenue + installation_revenue)
    total_cost = quantize_money(recurring_cost + installation_cost + normalized_fixed_cost)
    total_margin = quantize_money(total_revenue - total_cost)
    margin_percent = gross_margin_percent(total_revenue, total_cost)

    monthly_revenue = quantize_money(monthly_sale_vehicle * vehicle_count)
    monthly_cost = quantize_money(monthly_cost_vehicle * vehicle_count)
    monthly_margin = quantize_money(monthly_revenue - monthly_cost)

    installation_subsidy = quantize_money(
        installation_cost + (Decimal("0.00") if charge_installation else normalized_fixed_cost)
    )
    payback_months: Decimal | None = None
    if not charge_installation and monthly_margin > 0:
        payback_months = (installation_subsidy / monthly_margin).quantize(
            PERCENT_QUANT,
            rounding=ROUND_HALF_UP,
        )

    return {
        "vehicles": vehicle_count,
        "months": contract_months,
        "monthly_revenue": monthly_revenue,
        "monthly_cost": monthly_cost,
        "monthly_margin": monthly_margin,
        "recurring_revenue": recurring_revenue,
        "recurring_cost": recurring_cost,
        "installation_revenue": installation_revenue,
        "installation_cost": installation_cost,
        "fixed_cost": normalized_fixed_cost,
        "total_revenue": total_revenue,
        "total_cost": total_cost,
        "total_margin": total_margin,
        "margin_percent": margin_percent,
        "payback_months": payback_months,
    }


def break_even_vehicle_count(
    *,
    recurring_sale_per_vehicle: Any,
    recurring_cost_per_vehicle: Any,
    months: Any,
    installation_sale_per_vehicle: Any = 0,
    installation_cost_per_vehicle: Any = 0,
    charge_installation: bool = True,
    fixed_cost: Any = 0,
    target_margin_percent: Any = MIN_CUSTOM_MARGIN_PERCENT,
    maximum_vehicles: int = 100_000,
) -> int | None:
    """Retorna a quantidade mínima de veículos para atingir a margem-alvo.

    Quando não existe custo fixo, a margem percentual tende a permanecer igual
    para qualquer quantidade. Nesse caso, retorna 1 quando o cenário já atende
    ao piso ou ``None`` quando a estrutura unitária nunca o atende.
    """
    months_decimal = max(Decimal("1"), to_decimal(months, "1"))
    target = to_decimal(target_margin_percent) / Decimal("100")

    revenue_per_vehicle = quantize_money(
        to_decimal(recurring_sale_per_vehicle) * months_decimal
        + (to_decimal(installation_sale_per_vehicle) if charge_installation else Decimal("0"))
    )
    cost_per_vehicle = quantize_money(
        to_decimal(recurring_cost_per_vehicle) * months_decimal
        + to_decimal(installation_cost_per_vehicle)
    )
    normalized_fixed_cost = quantize_money(fixed_cost)

    if revenue_per_vehicle <= 0:
        return None

    contribution_for_target = revenue_per_vehicle * (Decimal("1") - target) - cost_per_vehicle
    if contribution_for_target <= 0:
        return None

    if normalized_fixed_cost <= 0:
        return 1

    minimum = (normalized_fixed_cost / contribution_for_target).to_integral_value(rounding=ROUND_CEILING)
    result = max(1, int(minimum))
    return result if result <= maximum_vehicles else None


def quantity_scenarios(
    quantities: Iterable[int],
    *,
    recurring_sale_per_vehicle: Any,
    recurring_cost_per_vehicle: Any,
    months: Any,
    installation_sale_per_vehicle: Any = 0,
    installation_cost_per_vehicle: Any = 0,
    charge_installation: bool = True,
    fixed_cost: Any = 0,
) -> list[dict[str, float | int | None]]:
    """Gera cenários consolidados por tamanho de frota."""
    rows: list[dict[str, float | int | None]] = []
    normalized_quantities = sorted({max(1, int(quantity)) for quantity in quantities})
    for quantity in normalized_quantities:
        totals = proposal_totals(
            recurring_sale_per_vehicle=recurring_sale_per_vehicle,
            recurring_cost_per_vehicle=recurring_cost_per_vehicle,
            months=months,
            vehicles=quantity,
            installation_sale_per_vehicle=installation_sale_per_vehicle,
            installation_cost_per_vehicle=installation_cost_per_vehicle,
            charge_installation=charge_installation,
            fixed_cost=fixed_cost,
        )
        rows.append(
            {
                "Veículos": quantity,
                "Receita do contrato": float(totals["total_revenue"] or 0),
                "Custo total": float(totals["total_cost"] or 0),
                "Margem total": float(totals["total_margin"] or 0),
                "Margem (%)": (
                    float(totals["margin_percent"])
                    if totals["margin_percent"] is not None
                    else None
                ),
                "Payback instalação (meses)": (
                    float(totals["payback_months"])
                    if totals["payback_months"] is not None
                    else None
                ),
            }
        )
    return rows
