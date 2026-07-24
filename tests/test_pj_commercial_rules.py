from decimal import Decimal

from app_core.pricing import (
    MIN_CUSTOM_MARGIN_PERCENT,
    break_even_vehicle_count,
    gross_margin_percent,
    minimum_sale_price,
    proposal_totals,
    sale_price_from_margin,
    validate_minimum_margin,
)


def test_custom_margin_never_accepts_less_than_thirty_percent():
    assert MIN_CUSTOM_MARGIN_PERCENT == Decimal("30.00")
    try:
        sale_price_from_margin(70, 29.99)
    except ValueError:
        pass
    else:
        raise AssertionError("Margem abaixo de 30% deveria ser rejeitada.")


def test_custom_value_floor_preserves_thirty_percent_margin():
    floor = minimum_sale_price(70, 30)
    assert floor == Decimal("100.00")
    valid, percent = validate_minimum_margin(floor, 70, 30)
    assert valid is True
    assert percent == Decimal("30.00")
    assert gross_margin_percent(99.99, 70) < Decimal("30.00")


def test_installation_waiver_keeps_internal_cost_in_margin():
    charged = proposal_totals(
        recurring_sale_per_vehicle=100,
        recurring_cost_per_vehicle=60,
        months=12,
        vehicles=10,
        installation_sale_per_vehicle=150,
        installation_cost_per_vehicle=100,
        charge_installation=True,
        fixed_cost=500,
    )
    waived = proposal_totals(
        recurring_sale_per_vehicle=100,
        recurring_cost_per_vehicle=60,
        months=12,
        vehicles=10,
        installation_sale_per_vehicle=150,
        installation_cost_per_vehicle=100,
        charge_installation=False,
        fixed_cost=500,
    )
    assert charged["installation_revenue"] == Decimal("1500.00")
    assert waived["installation_revenue"] == Decimal("0.00")
    assert charged["installation_cost"] == waived["installation_cost"] == Decimal("1000.00")
    assert charged["total_margin"] - waived["total_margin"] == Decimal("1500.00")


def test_break_even_uses_fixed_cost_and_vehicle_quantity():
    minimum = break_even_vehicle_count(
        recurring_sale_per_vehicle=100,
        recurring_cost_per_vehicle=60,
        months=12,
        installation_sale_per_vehicle=0,
        installation_cost_per_vehicle=100,
        charge_installation=False,
        fixed_cost=1000,
        target_margin_percent=30,
    )
    assert minimum is not None
    assert minimum > 1
