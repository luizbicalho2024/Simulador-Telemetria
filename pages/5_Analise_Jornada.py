# pages/🚛_Analise_Jornada.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
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
        transition: transform 0.1s ease-in-out, box-shadow 0.1s;
    }
    .compact-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    /* Cores das Bordas */
    .border-critical { border-left-color: #d32f2f; } /* Vermelho */
    .border-warning { border-left-color: #f57c00; }  /* Laranja */
    
    /* Tipografia do Card */
    .card-title {
        font-size: 16px;
        font-weight: 600;
        color: #333;
        margin: 0;
        display: flex;
        justify-content: space-between;
    }
    .card-meta {
        font-size: 12px;
        color: #666;
        margin-top: 4px;
    }
    .card-violation {
        font-size: 13px;
        color: #d32f2f;
        font-weight: 500;
        margin-top: 6px;
    }
    
    /* Ajuste de Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: transparent;
        border-radius: 4px 4px 0px 0px;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# Autenticação
if not st.session_state.get("authentication_status"):
    st.error("🔒 Acesso Negado! Por favor, faça login.")
    st.stop()

# --- FUNÇÕES ---

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

def minutes_to_str(minutes):
    """Converte minutos inteiros de volta para HH:MM"""
    h = int(minutes // 60)
    m = int(minutes % 60)
    return f"{h:02d}:{m:02d}"

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
        
        # Regra Crítica: > 5h30 Condução
        if conducao_continua_min > 330:
            violacoes_criticas.append(f"Direção Ininterrupta: {row['Max_Conducao_Continua']} (Limite 05:30)")
            status = "Crítico"

        # Regra Secundária: < 11h Interjornada
        if 0 < interjornada_min < 650:
            violacoes_secundarias.append(f"Interjornada Curta: {row['Interjornada']} (Mín 11:00)")
            if status == "Conforme": status = "Atenção"

        resultados.append({
            "Motorista": row['Motorista'],
            "Data_Ref": f"{row['Dia']} ({row['Semana']})",
            "Dia_Num": int(row['Dia']), # Para ordenação gráfica
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
        total_criticos = len(df_criticos)
        total_atencao = len(df_analise[df_analise['Tem_Atencao'] == True])
        
        # --- KPIs ---
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Motoristas", df_analise['Motorista'].nunique())
        c2.metric("Dias Analisados", len(df_analise))
        c3.metric("Violações Críticas (Condução)", total_criticos, delta_color="inverse")
        c4.metric("Pontos de Atenção (Interjornada)", total_atencao, delta_color="inverse")
        
        st.markdown("---")

        tab1, tab2, tab3 = st.tabs(["🚨 Gestão de Risco", "📊 Inteligência de Dados", "📋 Lista Detalhada"])

        # --- TAB 1: CARDs COMPACTOS ---
        with tab1:
            c_left, c_right = st.columns([1, 1])
            
            with c_left:
                st.subheader("🔴 Crítico: Excesso de Direção")
                st.caption("Motoristas que dirigiram mais de 5h30 sem parar.")
                
                if not df_criticos.empty:
                    # Filtro por motorista
                    motoristas_criticos = df_criticos['Motorista'].unique()
                    filtro_mot = st.multiselect("Filtrar Motorista:", options=motoristas_criticos, default=motoristas_criticos[:5])
                    
                    df_show_crit = df_criticos[df_criticos['Motorista'].isin(filtro_mot)]
                    
                    for idx, row in df_show_crit.iterrows():
                        # HTML Card Compacto Vermelho
                        st.markdown(f"""
                        <div class="compact-card border-critical">
                            <div class="card-title">
                                <span>{row['Motorista']}</span>
                                <span style="font-size: 14px; color: #666;">{row['Data_Ref']}</span>
                            </div>
                            <div class="card-violation">⚠️ {row['Critica_Msg']}</div>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.success("Nenhuma violação crítica encontrada.")

            with c_right:
                st.subheader("🟠 Atenção: Interjornada")
                st.caption("Descanso entre jornadas inferior a 11 horas.")
                
                df_atencao = df_analise[df_analise['Tem_Atencao'] == True]
                
                if not df_atencao.empty:
                    with st.container(height=500): # Scrollable container
                        for idx, row in df_atencao.iterrows():
                            # HTML Card Compacto Laranja
                            st.markdown(f"""
                            <div class="compact-card border-warning">
                                <div class="card-title">
                                    <span>{row['Motorista']}</span>
                                    <span style="font-size: 14px; color: #666;">{row['Data_Ref']}</span>
                                </div>
                                <div class="card-meta">
                                    <span style="color: #e65100;">{row['Secundaria_Msg']}</span>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                else:
                    st.info("Interjornadas conformes.")

        # --- TAB 2: GRÁFICOS ANALÍTICOS ---
        with tab2:
            st.subheader("Análise de Tendências e Risco")
            
            col_g1, col_g2 = st.columns([2, 1])
            
            with col_g1:
                # 1. SCATTER PLOT: Correlação Cansaço vs Infrações
                # Eixo X: Tamanho da Jornada Total
                # Eixo Y: Tempo Máximo de Condução Contínua
                # Cor: Status (Crítico/Conforme)
                # Objetivo: Mostrar que jornadas longas tendem a gerar infrações de condução
                
                fig_scatter = px.scatter(
                    df_analise, 
                    x="Jornada_Total_Min", 
                    y="Conducao_Continua_Min",
                    color="Status",
                    color_discrete_map={"Conforme": "#aaddaa", "Atenção": "#ffcc80", "Crítico": "#ff5252"},
                    hover_data=["Motorista", "Data_Ref", "Max_Conducao_Continua"],
                    title="Relação: Duração da Jornada vs Tempo ao Volante",
                    labels={"Jornada_Total_Min": "Jornada Total (min)", "Conducao_Continua_Min": "Máx. Volante sem Parar (min)"}
                )
                # Adiciona linha de limite 330min (5h30)
                fig_scatter.add_hline(y=330, line_dash="dash", line_color="red", annotation_text="Limite Lei (5h30)")
                st.plotly_chart(fig_scatter, use_container_width=True)

            with col_g2:
                # 2. BAR CHART: Top Infratores
                infratores = df_criticos['Motorista'].value_counts().reset_index()
                infratores.columns = ['Motorista', 'Qtd']
                
                if not infratores.empty:
                    fig_bar = px.bar(
                        infratores.head(10), 
                        x='Qtd', 
                        y='Motorista', 
                        orientation='h',
                        title="Top Infratores (Condução)",
                        color_discrete_sequence=['#d32f2f']
                    )
                    fig_bar.update_layout(yaxis={'categoryorder':'total ascending'})
                    st.plotly_chart(fig_bar, use_container_width=True)
                else:
                    st.info("Sem dados para ranking.")

            # 3. HEATMAP / DISTRIBUIÇÃO DIÁRIA
            st.markdown("#### 📅 Distribuição de Ocorrências no Mês")
            # Agrupar violações por dia do mês
            violacoes_por_dia = df_criticos.groupby('Dia_Num').size().reset_index(name='Qtd')
            # Garantir que todos os dias até 31 apareçam (opcional, mas bom visualmente)
            
            if not violacoes_por_dia.empty:
                fig_line = px.area(
                    violacoes_por_dia, 
                    x='Dia_Num', 
                    y='Qtd', 
                    title="Volume de Infrações Críticas por Dia do Mês",
                    markers=True,
                    color_discrete_sequence=['#ff5252']
                )
                fig_line.update_xaxes(dtick=1) # Mostrar todos os dias
                st.plotly_chart(fig_line, use_container_width=True)

        # --- TAB 3: DADOS ---
        with tab3:
            st.dataframe(
                df_analise[['Motorista', 'Data_Ref', 'Status', 'Max_Conducao_Continua', 'Interjornada', 'Critica_Msg', 'Secundaria_Msg']],
                use_container_width=True
            )

    else:
        st.error("Erro ao ler dados.")
