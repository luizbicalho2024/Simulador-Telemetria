from pathlib import Path


def test_pj_ui_uses_compact_controls_and_amcharts() -> None:
    source = Path("pages/1_Simulador_PJ.py").read_text(encoding="utf-8")

    assert 'with st.popover("Ajustar")' in source
    assert "cdn.amcharts.com/lib/version/5.20.3/index.js" in source
    assert "cdn.amcharts.com/lib/version/5.20.3/xy.js" in source
    assert "cdn.amcharts.com/lib/version/5.20.3/themes/Animated.js" in source
    assert '[/]\\n{valueX}' not in source
    assert "showChartError" in source
    assert "_render_break_even_chart(" in source
    assert 'with st.expander("Ver tabela detalhada do cenário")' in source
