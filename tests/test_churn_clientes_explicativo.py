import re
from pathlib import Path


def test_churn_movement_labels_are_clear() -> None:
    source = Path("pages/13_Churn_Clientes.py").read_text(
        encoding="utf-8"
    )

    assert '"Churn total": "Cliente perdido"' in source
    assert '"Contração": "Reduziu a base"' in source
    assert '"Estável": "Manteve a base"' in source
    assert '"Sem movimento": "Sem base nos dois meses"' in source
    assert "format_func=_movement_label" in source
    assert "Entenda todos os movimentos" in source


def test_impact_chart_no_longer_sends_negative_values_left() -> None:
    source = Path("pages/13_Churn_Clientes.py").read_text(
        encoding="utf-8"
    )

    match = re.search(
        r'if \(kind === "impact"\) \{(.*?)'
        r'if \(kind === "mix"\) \{',
        source,
        flags=re.S,
    )
    assert match is not None

    impact_block = match.group(1)

    assert 'valueXField: "impactMagnitude"' in impact_block
    assert 'valueXField: "deltaRevenue"' not in impact_block
    assert "min: 0" in impact_block
    assert "directionLabel" in impact_block
    assert "description" in impact_block
    assert '"impactMagnitude": abs(delta)' in source
    assert "Todas as barras crescem para a direita" in source
    assert "Verde = ganho de receita" in source


def test_churn_page_explains_stable_vs_no_movement() -> None:
    source = Path("pages/13_Churn_Clientes.py").read_text(
        encoding="utf-8"
    )

    assert "Manteve a base (Estável)" in source
    assert "Sem base nos dois meses (Sem movimento)" in source
    assert "Clientes perdidos" in source
    assert "Veículos de clientes perdidos" in source
    assert "Veículos que saíram da base" in source


def test_complete_clients_table_colors_revenue_variation() -> None:
    source = Path("pages/13_Churn_Clientes.py").read_text(
        encoding="utf-8"
    )

    assert "def _delta_cell_style" in source
    assert "rgba(22, 163, 74, 0.16)" in source
    assert "rgba(220, 38, 38, 0.16)" in source
    assert "_style_churn_table(detail_display)" in source
    assert '"Variação da receita"' in source
    assert '"Variação da receita (%)"' in source
