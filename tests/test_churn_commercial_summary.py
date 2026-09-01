from pathlib import Path


def test_churn_summary_is_commercial_and_visual() -> None:
    source = Path("pages/13_Churn_Clientes.py").read_text(encoding="utf-8")
    assert "def _commercial_summary_cards(" in source
    assert "Resumo comercial do mês" in source
    assert "Resultado do mês" in source
    assert "Base de veículos" in source
    assert "Maior perda" in source
    assert "Maior ganho" in source
    assert "entradas /" in source
    assert "unsafe_allow_html=True" in source
    assert "def _executive_read(" not in source
    assert "Maior pressão negativa:" not in source
    assert "Maior contribuição positiva:" not in source


def test_churn_summary_escapes_client_names() -> None:
    source = Path("pages/13_Churn_Clientes.py").read_text(encoding="utf-8")
    assert "import html" in source
    assert "html.escape" in source
