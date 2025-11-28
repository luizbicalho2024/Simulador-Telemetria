# pages/🚛_Analise_Jornada.py
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from fpdf import FPDF
import io

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    layout="wide",
    page_title="Análise Lei do Motorista (13.103)",
    page_icon="🚛"
)

# --- CSS PERSONALIZADO (UI/UX) ---
st.markdown("""
    <style>
    /* KPIs */
    .metric-container {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 15px;
        text-align: center;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }
    /* CARDS COMPACTOS */
    .compact-card {
        background-color: #ffffff;
        border-radius: 8px;
        padding: 12px 16px;
        margin-bottom: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        border-left: 5px solid #ddd;
    }
    .border-critical { border-left-color: #d32f2f; }
    .border-warning { border-left-color: #f57c00; }
    
    .card-title { font-size: 16px; font-weight: 600; color: #333; display: flex; justify-content: space-between; }
    .card-violation { font-size: 13px; color: #d32f2f; font-weight: 500; margin-top: 6px; }
    
    /* Email Box */
    .email-box {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 5px;
        padding: 20px;
        font-family: monospace;
        white-space: pre-wrap;
    }
    </style>
""", unsafe_allow_html=True)

if not st.session_state.get("authentication_status"):
    st.error("🔒 Acesso Negado! Por favor, faça login.")
    st.stop()

# --- FUNÇÕES DE PROCESSAMENTO ---

def time_str_to_minutes(time_str):
    if pd.isna(time_str) or str(time_str).strip() == '' or str(time_str).strip() == '00:00:00':
        return 0
    try:
        if isinstance(time_str, (datetime, pd.Timestamp)):
            return time_str.hour * 60 + time_str.minute
        parts = str(time_str).split(':')
        if len(parts) >= 2:
            return int(parts[0]) * 60 + int(parts[1])
        return 0
    except:
        return 0

def processar_relatorio_complexo(file):
    try:
        if file.name.endswith('.csv'):
            try:
                df_raw = pd.read_csv(file, header=None, encoding='utf-8', sep=',')
            except:
                df_raw = pd.read_csv(file, header=None, encoding='latin1', sep=',')
        else:
            df_raw = pd.read_excel(file, header=None)

        dados_processados = []
        motorista_atual = None
        
        for index, row in df_raw.iterrows():
            row_list = [str(x).strip() for x in row.values]
            row_list = [x if x.lower() != 'nan' else '' for x in row_list]

            if len(row_list) > 2 and row_list[1] and row_list[1].lower() not in ['dia do mês', 'nome', '', 'jornada de motorista']:
                if not row_list[1][0].isdigit() and row_list[2] == '':
                    motorista_atual = row_list[1]
                    continue
            
            if len(row_list) > 13 and motorista_atual:
                dia_mes = row_list[1]
                if dia_mes.isdigit() and 1 <= int(dia_mes) <= 31:
                    dados_processados.append({
                        "Motorista": motorista_atual,
                        "Dia": dia_mes,
                        "Semana": row_list[2],
                        "Inicio_Jornada": row_list[3],
                        "Fim_Jornada": row_list[4],
                        "Jornada_Total": row_list[5],
                        "Conducao_Total": row_list[6],
                        "Max_Conducao_Continua": row_list[9], 
                        "Espera": row_list[10],
                        "Refeicao": row_list[11],
                        "Descanso": row_list[12],
                        "Interjornada": row_list[13]
                    })
        return pd.DataFrame(dados_processados)
    except Exception as e:
        st.error(f"Erro ao processar: {e}")
        return None

def analisar_conformidade(df):
    resultados = []
    
    for idx, row in df.iterrows():
        violacoes_criticas = [] 
        violacoes_secundarias = [] 
        status = "Conforme"
        
        interjornada_min = time_str_to_minutes(row['Interjornada'])
        conducao_continua_min = time_str_to_minutes(row['Max_Conducao_Continua'])
        jornada_total_min = time_str_to_minutes(row['Jornada_Total'])
        
        if conducao_continua_min > 330:
            violacoes_criticas.append(f"Direção Ininterrupta: {row['Max_Conducao_Continua']} (Limite 05:30)")
            status = "Crítico"

        if 0 < interjornada_min < 650:
            violacoes_secundarias.append(f"Interjornada Curta: {row['Interjornada']} (Mín 11:00)")
            if status == "Conforme": status = "Atenção"

        resultados.append({
            "Motorista": row['Motorista'],
            "Data_Ref": f"{row['Dia']} ({row['Semana']})",
            "Dia_Num": int(row['Dia']),
            "Status": status,
            "Critica_Msg": violacoes_criticas[0] if violacoes_criticas else "",
            "Secundaria_Msg": violacoes_secundarias[0] if violacoes_secundarias else "",
            "Tem_Critica": len(violacoes_criticas) > 0,
            "Tem_Atencao": len(violacoes_secundarias) > 0,
            "Jornada_Total_Min": jornada_total_min,
            "Conducao_Continua_Min": conducao_continua_min,
            "Max_Conducao_Continua": row['Max_Conducao_Continua'],
            "Interjornada": row['Interjornada']
        })
        
    return pd.DataFrame(resultados)

# --- FUNÇÃO DE GERAÇÃO DE PDF ---
def create_pdf_report(df_criticos, df_atencao, total_dias, total_motoristas):
    class PDF(FPDF):
        def header(self):
            self.set_font('Arial', 'B', 15)
            self.cell(0, 10, 'Relatório de Auditoria de Jornada (Lei 13.103)', 0, 1, 'C')
            self.ln(5)
        
        def footer(self):
            self.set_y(-15)
            self.set_font('Arial', 'I', 8)
            self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')

    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    # Resumo
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "Resumo Executivo", 0, 1)
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 8, f"Dias Analisados: {total_dias}", 0, 1)
    pdf.cell(0, 8, f"Motoristas Auditados: {total_motoristas}", 0, 1)
    pdf.cell(0, 8, f"Total de Infrações Críticas (Condução > 5h30): {len(df_criticos)}", 0, 1)
    pdf.cell(0, 8, f"Total de Pontos de Atenção (Interjornada < 11h): {len(df_atencao)}", 0, 1)
    pdf.ln(10)
    
    # Detalhes Críticos
    if not df_criticos.empty:
        pdf.set_font("Arial", 'B', 12)
        pdf.set_text_color(200, 0, 0)
        pdf.cell(0, 10, "INFRAÇÕES CRÍTICAS (Excesso de Direção)", 0, 1)
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Arial", size=10)
        
        # Cabeçalho da tabela
        pdf.cell(60, 8, "Motorista", 1)
        pdf.cell(40, 8, "Data", 1)
        pdf.cell(90, 8, "Detalhe", 1)
        pdf.ln()
        
        for idx, row in df_criticos.iterrows():
            # Tenta codificar para latin-1 para aceitar acentos, remove se falhar
            try:
                mot = row['Motorista'].encode('latin-1', 'replace').decode('latin-1')
                detalhe = row['Critica_Msg'].encode('latin-1', 'replace').decode('latin-1')
                data = row['Data_Ref'].encode('latin-1', 'replace').decode('latin-1')
            except:
                mot = row['Motorista']
                detalhe = row['Critica_Msg']
                data = row['Data_Ref']

            pdf.cell(60, 8, mot[:28], 1)
            pdf.cell(40, 8, data, 1)
            pdf.cell(90, 8, detalhe, 1)
            pdf.ln()
        pdf.ln(10)

    # Detalhes Atenção
    if not df_atencao.empty:
        pdf.set_font("Arial", 'B', 12)
        pdf.set_text_color(255, 140, 0)
        pdf.cell(0, 10, "PONTOS DE ATENÇÃO (Interjornada)", 0, 1)
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Arial", size=10)
        
        pdf.cell(60, 8, "Motorista", 1)
        pdf.cell(40, 8, "Data", 1)
        pdf.cell(90, 8, "Detalhe", 1)
        pdf.ln()
        
        for idx, row in df_atencao.iterrows():
            try:
                mot = row['Motorista'].encode('latin-1', 'replace').decode('latin-1')
                detalhe = row['Secundaria_Msg'].encode('latin-1', 'replace').decode('latin-1')
                data = row['Data_Ref'].encode('latin-1', 'replace').decode('latin-1')
            except:
                mot = row['Motorista']
                detalhe = row['Secundaria_Msg']
                data = row['Data_Ref']

            pdf.cell(60, 8, mot[:28], 1)
            pdf.cell(40, 8, data, 1)
            pdf.cell(90, 8, detalhe, 1)
            pdf.ln()

    return pdf.output(dest='S').encode('latin-1')

# --- UI PRINCIPAL ---

st.title("🚛 Analytics de Jornada")
st.markdown("Painel gerencial de conformidade com a Lei do Motorista 13.103.")

uploaded_file = st.file_uploader("Upload Relatório de Jornada", type=['xlsx', 'csv'], label_visibility="collapsed")

if uploaded_file:
    df_flat = processar_relatorio_complexo(uploaded_file)
    
    if df_flat is not None and not df_flat.empty:
        df_analise = analisar_conformidade(df_flat)
        
        # Filtros
        df_criticos = df_analise[df_analise['Tem_Critica'] == True]
        df_atencao = df_analise[df_analise['Tem_Atencao'] == True]
        
        total_criticos = len(df_criticos)
        total_atencao = len(df_atencao)
        
        # --- KPIs ---
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Motoristas", df_analise['Motorista'].nunique())
        c2.metric("Dias Analisados", len(df_analise))
        c3.metric("Violações Críticas", total_criticos, delta_color="inverse")
        c4.metric("Pontos de Atenção", total_atencao, delta_color="inverse")
        
        st.markdown("---")

        tab1, tab2, tab3, tab4 = st.tabs(["🚨 Gestão de Risco", "📊 Inteligência de Dados", "📋 Lista Detalhada", "📧 Comunicar Gestor"])

        # --- TAB 1: RISCO ---
        with tab1:
            c_left, c_right = st.columns([1, 1])
            with c_left:
                st.subheader("🔴 Crítico: Excesso de Direção")
                if not df_criticos.empty:
                    motoristas_criticos = df_criticos['Motorista'].unique()
                    filtro_mot = st.multiselect("Filtrar Motorista:", options=motoristas_criticos, default=motoristas_criticos[:5])
                    df_show_crit = df_criticos[df_criticos['Motorista'].isin(filtro_mot)]
                    for idx, row in df_show_crit.iterrows():
                        st.markdown(f"""
                        <div class="compact-card border-critical">
                            <div class="card-title"><span>{row['Motorista']}</span><span style="font-size:14px;color:#666;">{row['Data_Ref']}</span></div>
                            <div class="card-violation">⚠️ {row['Critica_Msg']}</div>
                        </div>""", unsafe_allow_html=True)
                else:
                    st.success("Nenhuma violação crítica encontrada.")

            with c_right:
                st.subheader("🟠 Atenção: Interjornada")
                if not df_atencao.empty:
                    with st.container(height=500):
                        for idx, row in df_atencao.iterrows():
                            st.markdown(f"""
                            <div class="compact-card border-warning">
                                <div class="card-title"><span>{row['Motorista']}</span><span style="font-size:14px;color:#666;">{row['Data_Ref']}</span></div>
                                <div class="card-violation" style="color:#e65100">{row['Secundaria_Msg']}</div>
                            </div>""", unsafe_allow_html=True)
                else:
                    st.info("Interjornadas conformes.")

        # --- TAB 2: GRÁFICOS ---
        with tab2:
            col_g1, col_g2 = st.columns([2, 1])
            with col_g1:
                fig_scatter = px.scatter(
                    df_analise, x="Jornada_Total_Min", y="Conducao_Continua_Min", color="Status",
                    color_discrete_map={"Conforme": "#aaddaa", "Atenção": "#ffcc80", "Crítico": "#ff5252"},
                    hover_data=["Motorista", "Data_Ref", "Max_Conducao_Continua"],
                    title="Relação: Duração da Jornada vs Tempo ao Volante"
                )
                fig_scatter.add_hline(y=330, line_dash="dash", line_color="red", annotation_text="Limite Lei (5h30)")
                st.plotly_chart(fig_scatter, use_container_width=True)

            with col_g2:
                infratores = df_criticos['Motorista'].value_counts().reset_index()
                infratores.columns = ['Motorista', 'Qtd']
                if not infratores.empty:
                    fig_bar = px.bar(infratores.head(10), x='Qtd', y='Motorista', orientation='h', title="Top Infratores", color_discrete_sequence=['#d32f2f'])
                    fig_bar.update_layout(yaxis={'categoryorder':'total ascending'})
                    st.plotly_chart(fig_bar, use_container_width=True)
                else:
                    st.info("Sem dados para ranking.")

        # --- TAB 3: DADOS ---
        with tab3:
            st.dataframe(df_analise[['Motorista', 'Data_Ref', 'Status', 'Max_Conducao_Continua', 'Interjornada', 'Critica_Msg', 'Secundaria_Msg']], use_container_width=True)

        # --- TAB 4: EMAIL & PDF ---
        with tab4:
            st.header("📧 Central de Comunicação")
            st.markdown("Gere um email padrão para o gestor da frota e anexe o relatório PDF.")

            # Preparar Dados para o Email
            mes_referencia = datetime.now().strftime("%B/%Y")
            top_infratores_lista = ""
            if not df_criticos.empty:
                top_3 = df_criticos['Motorista'].value_counts().head(3).index.tolist()
                top_infratores_lista = "\n".join([f"   - {m}" for m in top_3])
            else:
                top_infratores_lista = "   - Nenhum motorista crítico identificado."

            # Template do Email
            email_subject = f"Relatório de Auditoria de Jornada - {mes_referencia} - Ação Requerida"
            email_body = f"""Olá Gestor,

Segue o resumo da auditoria de jornada (Lei 13.103) referente aos dados processados recentemente.

RESUMO EXECUTIVO:
------------------------------------------------
- Total de Motoristas Analisados: {df_analise['Motorista'].nunique()}
- Violações Críticas (Direção > 5h30): {total_criticos}
- Pontos de Atenção (Interjornada < 11h): {total_atencao}

MOTORISTAS COM MAIOR RISCO (Top 3):
{top_infratores_lista}

AÇÃO NECESSÁRIA:
Por favor, analise o relatório PDF em anexo para visualizar os detalhes de cada ocorrência e tome as medidas corretivas necessárias para garantir a conformidade legal e a segurança da operação.

Atenciosamente,
Sistema de Gestão de Frotas"""

            col_email, col_anexo = st.columns([2, 1])

            with col_email:
                st.subheader("1. Texto do Email")
                st.text_area("Copie o texto abaixo:", value=email_body, height=350)
                st.info("💡 Dica: Você pode copiar e colar este texto diretamente no seu cliente de email (Outlook, Gmail).")

            with col_anexo:
                st.subheader("2. Anexos")
                st.write("Baixe o relatório oficial para anexar ao email.")
                
                # Gerar PDF
                try:
                    pdf_bytes = create_pdf_report(df_criticos, df_atencao, len(df_analise), df_analise['Motorista'].nunique())
                    st.download_button(
                        label="📥 Baixar Relatório PDF",
                        data=pdf_bytes,
                        file_name="Relatorio_Auditoria_Jornada.pdf",
                        mime="application/pdf",
                        type="primary",
                        use_container_width=True
                    )
                except Exception as e:
                    st.error(f"Erro ao gerar PDF (verifique se 'fpdf' está instalado): {e}")
                
                st.markdown("---")
                st.caption("**Dica:** Para incluir os gráficos, você pode tirar um 'print' da aba 'Inteligência de Dados' ou clicar no ícone de câmera que aparece ao passar o mouse sobre os gráficos.")

    else:
        st.error("Erro ao ler dados.")
