from decimal import Decimal
from pathlib import Path

from app_core.pricing import (
    proposal_totals,
    summarize_cost_components,
)
from config import normalize_pricing_config


def test_detailed_cost_summary_separates_monthly_and_one_time() -> None:
    summary = summarize_cost_components(
        [
            {
                "despesa": "Conectividade",
                "incidencia": "Mensal por veículo",
                "valor": 12.50,
            },
            {
                "despesa": "Rastreador",
                "incidencia": "Único por veículo",
                "valor": 240.00,
            },
            {
                "despesa": "Acessório",
                "incidencia": "Único por veículo",
                "valor": 60.00,
            },
        ],
        12,
    )

    assert summary["recurring_monthly"] == Decimal("12.50")
    assert summary["one_time_per_vehicle"] == Decimal("300.00")
    assert summary["monthly_equivalent"] == Decimal("37.50")


def test_proposal_totals_count_one_time_cost_once() -> None:
    result = proposal_totals(
        recurring_sale_per_vehicle="80.00",
        recurring_cost_per_vehicle="12.50",
        one_time_cost_per_vehicle="300.00",
        months=12,
        vehicles=1,
        installation_sale_per_vehicle=0,
        installation_cost_per_vehicle=0,
        fixed_cost=0,
    )

    assert result["recurring_revenue"] == Decimal("960.00")
    assert result["recurring_cost"] == Decimal("150.00")
    assert result["one_time_cost"] == Decimal("300.00")
    assert result["total_cost"] == Decimal("450.00")
    assert result["total_margin"] == Decimal("510.00")


def test_pricing_config_preserves_detailed_costs() -> None:
    normalized = normalize_pricing_config(
        {
            "_id": "global_prices",
            "PLANOS_PJ": {
                "12 Meses": {"Rastreador X": 80.00},
            },
            "CUSTOS_DETALHADOS_PJ": {
                "Rastreador X": [
                    {
                        "despesa": "Hardware",
                        "incidencia": "Único por veículo",
                        "valor": 180,
                        "observacao": "Compra",
                    },
                    {
                        "despesa": "Chip",
                        "incidencia": "Mensal por veículo",
                        "valor": 8.5,
                    },
                ]
            },
        }
    )

    rows = normalized["CUSTOS_DETALHADOS_PJ"]["Rastreador X"]
    assert len(rows) == 2
    assert rows[0]["despesa"] == "Hardware"
    assert rows[0]["valor"] == 180.0
    assert rows[1]["incidencia"] == "Mensal por veículo"


def test_admin_exposes_dynamic_cost_composition() -> None:
    source = Path("Simulador_Comercial.py").read_text(encoding="utf-8")

    assert "Composição real de custos por rastreador" in source
    assert 'num_rows="dynamic"' in source
    assert "CUSTOS_DETALHADOS_PJ" in source
    assert "Custo mensal equivalente" in source
    assert "Único por veículo" in source


def test_pj_simulator_uses_detailed_costs() -> None:
    source = Path("pages/1_Simulador_PJ.py").read_text(encoding="utf-8")

    assert "detailed_costs_by_product" in source
    assert "summarize_cost_components" in source
    assert "one_time_cost_per_vehicle" in source
    assert "Custo único dos rastreadores" in source
    assert '"composicao_custos"' in source
