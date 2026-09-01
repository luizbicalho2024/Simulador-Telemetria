from decimal import Decimal
from pathlib import Path

from app_core.pricing import (
    mixed_break_even_vehicle_count,
    mixed_proposal_totals,
    mixed_quantity_scenarios,
)


def sample_mix() -> list[dict]:
    return [
        {
            "product": "GPRS",
            "quantity": 20,
            "recurring_sale": "80",
            "recurring_cost": "30",
            "one_time_cost": "100",
            "installation_sale": "100",
            "installation_cost": "80",
        },
        {
            "product": "Satélite",
            "quantity": 5,
            "recurring_sale": "200",
            "recurring_cost": "100",
            "one_time_cost": "500",
            "installation_sale": "100",
            "installation_cost": "80",
        },
        {
            "product": "Vídeo",
            "quantity": 2,
            "recurring_sale": "400",
            "recurring_cost": "200",
            "one_time_cost": "1000",
            "installation_sale": "200",
            "installation_cost": "150",
        },
    ]


def test_mixed_quantities_use_each_product_quantity() -> None:
    result = mixed_proposal_totals(
        items=sample_mix(),
        months=12,
        charge_installation=True,
        fixed_cost=900,
    )

    assert result["monthly_revenue"] == Decimal("3400.00")
    assert result["monthly_cost"] == Decimal("1500.00")
    assert result["recurring_revenue"] == Decimal("40800.00")
    assert result["recurring_cost"] == Decimal("18000.00")
    assert result["one_time_cost"] == Decimal("6500.00")
    assert result["installation_revenue"] == Decimal("2900.00")
    assert result["installation_cost"] == Decimal("2300.00")
    assert result["fixed_cost"] == Decimal("900.00")
    assert result["total_revenue"] == Decimal("43700.00")
    assert result["total_cost"] == Decimal("27700.00")
    assert result["total_margin"] == Decimal("16000.00")


def test_quantities_can_overlap_same_fleet() -> None:
    result = mixed_proposal_totals(
        items=[
            {
                "quantity": 30,
                "recurring_sale": 50,
                "recurring_cost": 20,
            },
            {
                "quantity": 30,
                "recurring_sale": 15,
                "recurring_cost": 5,
            },
        ],
        months=12,
    )

    assert result["device_quantity"] == Decimal("60")
    assert result["monthly_revenue"] == Decimal("1950.00")


def test_mixed_scenario_preserves_proportions() -> None:
    rows = mixed_quantity_scenarios(
        [30, 60],
        items=sample_mix(),
        base_fleet_vehicles=30,
        months=12,
        charge_installation=True,
        fixed_cost=900,
    )

    current, doubled = rows
    assert current["Receita do contrato"] == 43700.0
    assert doubled["Receita do contrato"] == 87400.0
    assert doubled["Custo total"] == 54500.0


def test_mixed_break_even_returns_projection() -> None:
    result = mixed_break_even_vehicle_count(
        items=sample_mix(),
        base_fleet_vehicles=30,
        months=12,
        charge_installation=True,
        fixed_cost=900,
        target_margin_percent=30,
    )

    assert result is not None
    assert result >= 1


def test_page_has_quantity_per_product_and_no_fixed_ranges() -> None:
    source = Path("pages/1_Simulador_PJ.py").read_text(
        encoding="utf-8"
    )

    assert '"range": "R$ 49–69/mês"' not in source
    assert "preset['range']" not in source
    assert '"Qtd."' in source
    assert "pj_quantity_" in source
    assert '"quantity": quantity' in source
    assert "mixed_proposal_totals" in source
    assert "mixed_quantity_scenarios" in source
    assert "mix_dispositivos" in source
    assert '"quantidade": item_quantity' in source


def test_registered_item_margin_uses_equivalent_cost() -> None:
    source = Path("pages/1_Simulador_PJ.py").read_text(
        encoding="utf-8"
    )

    assert 'pricing_cost = quantize_money(item["pricing_cost"])' in source
    assert "gross_margin_value(\n                effective_price,\n                pricing_cost," in source
