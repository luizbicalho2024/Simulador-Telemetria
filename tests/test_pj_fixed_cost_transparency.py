from decimal import Decimal
from pathlib import Path

from app_core.pricing import proposal_totals


def test_user_example_is_explained_by_fixed_cost() -> None:
    final = proposal_totals(
        recurring_sale_per_vehicle="80.88",
        recurring_cost_per_vehicle="53.92",
        months=12,
        vehicles=1,
        installation_sale_per_vehicle="100",
        installation_cost_per_vehicle="80",
        charge_installation=True,
        fixed_cost="900",
    )
    operational = proposal_totals(
        recurring_sale_per_vehicle="80.88",
        recurring_cost_per_vehicle="53.92",
        months=12,
        vehicles=1,
        installation_sale_per_vehicle="100",
        installation_cost_per_vehicle="80",
        charge_installation=True,
        fixed_cost="0",
    )

    assert final["total_revenue"] == Decimal("1070.56")
    assert final["total_cost"] == Decimal("1627.04")
    assert final["total_margin"] == Decimal("-556.48")
    assert final["margin_percent"] == Decimal("-51.98")
    assert operational["total_cost"] == Decimal("727.04")
    assert operational["total_margin"] == Decimal("343.52")
    assert operational["margin_percent"] == Decimal("32.09")


def test_installation_payback_does_not_mix_fixed_proposal_cost() -> None:
    waived = proposal_totals(
        recurring_sale_per_vehicle="80.88",
        recurring_cost_per_vehicle="53.92",
        months=12,
        vehicles=1,
        installation_sale_per_vehicle="100",
        installation_cost_per_vehicle="80",
        charge_installation=False,
        fixed_cost="900",
    )
    assert waived["payback_months"] == Decimal("2.97")
    assert waived["total_cost"] == Decimal("1627.04")


def test_pj_page_explains_fixed_cost_policy_failure() -> None:
    source = Path("pages/1_Simulador_PJ.py").read_text(encoding="utf-8")
    assert "Margem operacional" in source
    assert "Custo fixo implantação" in source
    assert "fixed_cost_caused_policy_failure" in source
    assert "A oferta está dentro da política antes do custo fixo" in source
    assert "Custo fixo interno aplicado à proposta" in source
    assert '"chosen_operational_totals"' in source
    assert '"margem_operacional_percentual"' in source


def test_pj_admin_warns_about_global_fixed_cost() -> None:
    source = Path("Simulador_Comercial.py").read_text(encoding="utf-8")
    assert "Todas as propostas PJ receberão" in source
    assert "inclusive propostas de 1 veículo" in source
    assert "Use R$ 0,00" in source


def test_pj_amcharts_clears_host_before_rendering() -> None:
    source = Path("pages/1_Simulador_PJ.py").read_text(encoding="utf-8")
    assert "Carregando análise interativa de margem..." not in source
    assert "host.replaceChildren();" in source
    assert "const root = am5.Root.new(host);" in source
