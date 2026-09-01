from pathlib import Path


def test_churn_page_uses_amcharts_executive_dashboard() -> None:
    source = Path("pages/13_Churn_Clientes.py").read_text(encoding="utf-8")

    assert "streamlit.components.v1 as components" in source
    assert "cdn.amcharts.com/lib/version/5.20.3/index.js" in source
    assert "cdn.amcharts.com/lib/version/5.20.3/xy.js" in source
    assert "cdn.amcharts.com/lib/version/5.20.3/percent.js" in source
    assert "cdn.amcharts.com/lib/version/5.20.3/themes/Animated.js" in source
    assert 'if (kind === "impact")' in source
    assert 'if (kind === "mix")' in source
    assert 'if (kind === "overview")' in source
    assert 'if (kind === "moves")' in source
    assert 'if (kind === "movers")' in source
    assert "showChartError" in source
    assert "scope_metrics = metrics" in source
    assert '"Top clientes"' in source
    assert 'with st.expander("Ver tabela completa dos clientes"' in source
    assert "plotly.express" not in source
    assert "style_plotly_figure" not in source
    assert '[/]\\n' not in source
