from __future__ import annotations

import io
import unicodedata
from datetime import datetime, time, timedelta

import pandas as pd
import plotly.express as px
import streamlit as st
from fpdf import FPDF

import user_management_db as db
from app_core.auth import require_auth
from app_core.ui import apply_branding, configure_page, render_hero, render_sidebar

configure_page("Análise de Jornada")
branding = apply_branding()
require_auth()
render_sidebar()
render_hero("Análise de jornada", "Avalie direção contínua, interjornada e ocorrências indicativas de não conformidade.")
st.caption("A análise é gerencial e indicativa. Casos trabalhistas devem ser validados pelas áreas jurídica e de recursos humanos.")


def duration_to_minutes(value: object) -> int:
    if value is None or pd.isna(value):
        return 0
    if isinstance(value, pd.Timedelta):
        return max(0, int(value.total_seconds() // 60))
    if isinstance(value, timedelta):
        return max(0, int(value.total_seconds() // 60))
    if isinstance(value, (datetime, time, pd.Timestamp)):
        return int(value.hour * 60 + value.minute)
    if isinstance(value, (float, int)):
        # Valores de duração do Excel são frações de um dia.
        return max(0, int(round(float(value) * 24 * 60)))

    text = str(value).strip()
    if not text or text.lower() in {"nan", "nat", "00:00:00"}:
        return 0
    try:
        if "day" in text:
            return max(0, int(pd.to_timedelta(text).total_seconds() // 60))
        parts = text.split(":")
        if len(parts) >= 2:
            return max(0, int(float(parts[0])) * 60 + int(float(parts[1])))
    except (TypeError, ValueError):
        return 0
    return 0


@st.cache_data(show_spinner=False)
def process_report(file_bytes: bytes, filename: str) -> pd.DataFrame:
    buffer = io.BytesIO(file_bytes)
    if filename.lower().endswith(".csv"):
        try:
            raw = pd.read_csv(buffer, header=None, encoding="utf-8", sep=None, engine="python")
        except UnicodeDecodeError:
            buffer.seek(0)
            raw = pd.read_csv(buffer, header=None, encoding="latin-1", sep=None, engine="python")
    else:
        raw = pd.read_excel(buffer, header=None)

    records: list[dict] = []
    current_driver: str | None = None
    for _, row in raw.iterrows():
        values = ["" if pd.isna(value) else str(value).strip() for value in row.values]
        if len(values) > 2 and values[1] and values[1].lower() not in {"dia do mês", "nome", "jornada de motorista"}:
            if not values[1][0].isdigit() and values[2] == "":
                current_driver = values[1]
                continue
        if len(values) > 13 and current_driver:
            day = values[1]
            if day.isdigit() and 1 <= int(day) <= 31:
                records.append(
                    {
                        "Motorista": current_driver,
                        "Dia": int(day),
                        "Semana": values[2],
                        "Início da jornada": values[3],
                        "Fim da jornada": values[4],
                        "Jornada total": values[5],
                        "Condução total": values[6],
                        "Máxima condução contínua": values[9],
                        "Espera": values[10],
                        "Refeição": values[11],
                        "Descanso": values[12],
                        "Interjornada": values[13],
                    }
                )
    return pd.DataFrame(records)


def analyze_compliance(frame: pd.DataFrame) -> pd.DataFrame:
    records: list[dict] = []
    for _, row in frame.iterrows():
        continuous_minutes = duration_to_minutes(row["Máxima condução contínua"])
        interjourney_minutes = duration_to_minutes(row["Interjornada"])
        journey_minutes = duration_to_minutes(row["Jornada total"])

        critical_message = ""
        attention_message = ""
        status = "Conforme"
        if continuous_minutes > 330:
            critical_message = f"Direção contínua de {row['Máxima condução contínua']} — referência de 5h30 excedida"
            status = "Crítico"
        if 0 < interjourney_minutes < 660:
            attention_message = f"Interjornada de {row['Interjornada']} — referência mínima de 11h não atingida"
            if status == "Conforme":
                status = "Atenção"

        records.append(
            {
                "Motorista": row["Motorista"],
                "Data de referência": f"{row['Dia']} ({row['Semana']})",
                "Status": status,
                "Ocorrência crítica": critical_message,
                "Ponto de atenção": attention_message,
                "Tem crítica": bool(critical_message),
                "Tem atenção": bool(attention_message),
                "Jornada total (min)": journey_minutes,
                "Condução contínua (min)": continuous_minutes,
                "Máxima condução contínua": row["Máxima condução contínua"],
                "Interjornada": row["Interjornada"],
            }
        )
    return pd.DataFrame(records)


def _ascii(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value)).encode("latin-1", "ignore").decode("latin-1")
    return text


def create_pdf_report(critical: pd.DataFrame, attention: pd.DataFrame, total_days: int, total_drivers: int) -> bytes:
    class PDF(FPDF):
        def header(self):
            self.set_font("helvetica", "B", 14)
            self.cell(0, 10, "Relatorio de Auditoria de Jornada", new_x="LMARGIN", new_y="NEXT", align="C")
            self.ln(3)

        def footer(self):
            self.set_y(-15)
            self.set_font("helvetica", "I", 8)
            self.cell(0, 10, f"Pagina {self.page_no()}", align="C")

    pdf = PDF()
    pdf.add_page()
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 9, "Resumo executivo", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("helvetica", size=10)
    for line in (
        f"Dias analisados: {total_days}",
        f"Motoristas auditados: {total_drivers}",
        f"Ocorrencias criticas: {len(critical)}",
        f"Pontos de atencao: {len(attention)}",
    ):
        pdf.cell(0, 7, line, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)

    def add_section(title: str, frame: pd.DataFrame, message_column: str) -> None:
        if frame.empty:
            return
        pdf.set_font("helvetica", "B", 11)
        pdf.cell(0, 8, _ascii(title), new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("helvetica", size=8)
        for _, row in frame.iterrows():
            line = f"{_ascii(row['Motorista'])} | {_ascii(row['Data de referência'])} | {_ascii(row[message_column])}"
            pdf.multi_cell(0, 6, line, border=1)
        pdf.ln(4)

    add_section("Ocorrencias criticas", critical, "Ocorrência crítica")
    add_section("Pontos de atencao", attention, "Ponto de atenção")
    return bytes(pdf.output())


uploaded = st.file_uploader("Relatório de jornada", type=["xlsx", "csv"])
if uploaded:
    try:
        file_bytes = uploaded.getvalue()
        flat = process_report(file_bytes, uploaded.name)
        if flat.empty:
            st.error("Nenhuma linha de jornada foi identificada. Verifique a estrutura do relatório.")
            st.stop()

        analysis = analyze_compliance(flat)
        critical = analysis[analysis["Tem crítica"]]
        attention = analysis[analysis["Tem atenção"]]

        metrics = st.columns(4)
        metrics[0].metric("Motoristas", analysis["Motorista"].nunique())
        metrics[1].metric("Dias analisados", len(analysis))
        metrics[2].metric("Ocorrências críticas", len(critical))
        metrics[3].metric("Pontos de atenção", len(attention))

        tab_risk, tab_charts, tab_data, tab_communication = st.tabs(
            ["Gestão de risco", "Inteligência de dados", "Lista detalhada", "Comunicação"]
        )

        with tab_risk:
            critical_col, attention_col = st.columns(2)
            with critical_col:
                st.markdown("#### Excesso de direção contínua")
                if critical.empty:
                    st.success("Nenhuma ocorrência crítica foi identificada.")
                else:
                    drivers = critical["Motorista"].unique().tolist()
                    selected = st.multiselect("Motoristas", drivers, default=drivers[:5])
                    st.dataframe(
                        critical[critical["Motorista"].isin(selected)][["Motorista", "Data de referência", "Ocorrência crítica"]],
                        width="stretch",
                        hide_index=True,
                    )
            with attention_col:
                st.markdown("#### Interjornada")
                if attention.empty:
                    st.success("Nenhum ponto de atenção foi identificado.")
                else:
                    st.dataframe(
                        attention[["Motorista", "Data de referência", "Ponto de atenção"]],
                        width="stretch",
                        hide_index=True,
                    )

        with tab_charts:
            chart_col, rank_col = st.columns([2, 1])
            with chart_col:
                figure = px.scatter(
                    analysis,
                    x="Jornada total (min)",
                    y="Condução contínua (min)",
                    color="Status",
                    hover_data=["Motorista", "Data de referência", "Máxima condução contínua"],
                    title="Jornada total versus condução contínua",
                )
                figure.add_hline(y=330, line_dash="dash", annotation_text="Referência de 5h30")
                st.plotly_chart(figure, width="stretch")
            with rank_col:
                ranking = critical["Motorista"].value_counts().head(10).rename_axis("Motorista").reset_index(name="Ocorrências")
                if ranking.empty:
                    st.info("Sem ocorrências para ranking.")
                else:
                    rank_figure = px.bar(ranking, x="Ocorrências", y="Motorista", orientation="h", title="Motoristas com mais ocorrências")
                    rank_figure.update_traces(marker_color=branding["primary_color"])
                    rank_figure.update_layout(yaxis={"categoryorder": "total ascending"})
                    st.plotly_chart(rank_figure, width="stretch")

        with tab_data:
            st.dataframe(
                analysis[["Motorista", "Data de referência", "Status", "Máxima condução contínua", "Interjornada", "Ocorrência crítica", "Ponto de atenção"]],
                width="stretch",
                hide_index=True,
            )

        with tab_communication:
            top_drivers = critical["Motorista"].value_counts().head(3).index.tolist()
            top_lines = "\n".join(f"- {driver}" for driver in top_drivers) if top_drivers else "- Nenhum motorista crítico identificado"
            email_body = f"""Olá, gestor.

Segue o resumo da auditoria de jornada processada na plataforma.

Resumo:
- Motoristas analisados: {analysis['Motorista'].nunique()}
- Ocorrências críticas: {len(critical)}
- Pontos de atenção: {len(attention)}

Motoristas com maior concentração de ocorrências:
{top_lines}

Recomendamos a validação dos registros e a definição das ações operacionais aplicáveis.

Atenciosamente,
Equipe de Gestão de Frotas"""
            communication_col, report_col = st.columns([2, 1])
            with communication_col:
                st.text_area("Texto sugerido", value=email_body, height=330)
            with report_col:
                pdf_bytes = create_pdf_report(critical, attention, len(analysis), analysis["Motorista"].nunique())
                st.download_button(
                    "Baixar relatório em PDF",
                    data=pdf_bytes,
                    file_name="relatorio_auditoria_jornada.pdf",
                    mime="application/pdf",
                    type="primary",
                    width="stretch",
                )

        signature = f"{uploaded.name}:{len(file_bytes)}"
        if st.session_state.get("journey_analysis_logged") != signature:
            db.add_log(
                st.session_state.get("username", "sistema"),
                "Analisou jornada",
                {"motoristas": analysis["Motorista"].nunique(), "dias": len(analysis), "criticas": len(critical), "atencao": len(attention)},
            )
            st.session_state.journey_analysis_logged = signature
    except Exception as exc:
        st.error(f"Não foi possível analisar o relatório: {exc}")
else:
    st.caption("Carregue um relatório em XLSX ou CSV para iniciar a análise.")
