from pathlib import Path


def test_churn_amcharts_host_has_no_persistent_loading_placeholder() -> None:
    source = Path("pages/13_Churn_Clientes.py").read_text(encoding="utf-8")
    assert 'Carregando análise interativa...</div>' not in source
    assert '<div id="__CHART_ID__"></div>' in source
    assert 'host.replaceChildren();' in source
    assert 'const root = am5.Root.new(host);' in source


def test_churn_amcharts_host_has_fixed_geometry() -> None:
    source = Path("pages/13_Churn_Clientes.py").read_text(encoding="utf-8")
    assert 'min-height: __HEIGHT__px;' in source
    assert 'position: relative;' in source
    assert 'overflow: hidden;' in source
    assert '#__CHART_ID__ > div {' in source
    assert 'height: 100% !important;' in source


def test_churn_chart_error_fallback_still_exists() -> None:
    source = Path("pages/13_Churn_Clientes.py").read_text(encoding="utf-8")
    assert 'function showChartError(message)' in source
    assert 'Gráfico indisponível.' in source
