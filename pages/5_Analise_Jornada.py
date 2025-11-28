# pages/🚛_Analise_Jornada.py
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import io

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    layout="wide",
    page_title="Análise Lei do Motorista (13.103)",
    page_icon="🚛"
)

# --- ESTILOS CSS ---
st.markdown("""
    <style>
    .metric-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 15px;
        border-left: 5px solid #006494;
    }
    .violation-card-critical {
        background-color: #ffe6e6;
        border-radius: 8px;
        padding: 15px;
        color: #b30000;
        margin-bottom: 10px;
        border: 2px solid #ff4d4d;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
    }
    .violation-card-warning {
        background-color: #fff4e6;
        border-radius: 5px;
        padding: 10px;
        color: #cc7a00;
        margin-bottom: 5px;
        border: 1px solid #ffcc80;
    }
    </style>
""", unsafe_allow_html=True)

# Autenticação
if not st.session_state.get("authentication_status"):
    st.error("🔒 Acesso Negado! Por favor, faça login.")
    st.stop()

# --- FUNÇÕES DE PROCESSAMENTO ---

def time_str_to_minutes(time_str):
    """Converte string 'HH:MM:SS' para minutos totais."""
    if pd.isna(time_str) or str(time_str).strip() == '' or str(time_str).strip() == '00:00:00':
        return 0
    try:
        # Se vier como datetime do pandas/excel
        if isinstance(time_str, datetime) or isinstance(time_str, pd.Timestamp):
            return time_str.hour * 60 + time_str.minute
        
        # Se vier como string
        parts = str(time_str).split(':')
        if len(parts) >= 2:
            return int(parts[0]) * 60 + int(parts[1])
        return 0
    except:
        return 0

def processar_relatorio_complexo(file):
    """
    Lê o relatório CSV/Excel com estrutura aninhada (Motorista -> Dados)
    e transforma numa tabela plana (flat table) para análise.
    """
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

            # Identifica Motorista
            if len(row_list) > 2 and row_list[1] and row_list[1].lower() not in ['dia do mês', 'nome', '', 'jornada de motorista']:
                if not row_list[1][0].isdigit() and row_list[2] == '':
                    motorista_atual = row_list[1]
                    continue
            
            # Identifica Dados
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
        st.error(f"Erro ao processar estrutura do ficheiro. Detalhe: {e}")
        return None

def analisar_conformidade(df):
    """Aplica as regras da Lei 13.103 com foco na Condução Contínua."""
    resultados = []
    
    for idx, row in df.iterrows():
        violacoes_criticas = [] # Condução Contínua
        violacoes_secundarias = [] # Interjornada, etc.
        status = "Conforme"
        
        # Converter tempos para minutos
        interjornada_min = time_str_to_minutes(row['Interjornada'])
        conducao_continua_min = time_str_to_minutes(row['Max_Conducao_Continua'])
        
        # --- REGRA CRÍTICA: Condução Contínua (Máx 5h30 = 330 min) ---
        if conducao_continua_min > 330:
            violacoes_criticas.append(f"⚠️ EXCESSO GRAVE: Dirigiu {row['Max_Conducao_Continua']} sem parar (Limite Lei 13.103: 05:30)")
            status = "Violação Crítica"

        # --- REGRA SECUNDÁRIA: Interjornada (Mínimo 11h = 660 min) ---
        # Tolerância de 10 min
        if 0 < interjornada_min < 650:
            violacoes_secundarias.append(f"Interjornada insuficiente: {row['Interjornada']} (Mín exigido: 11:00)")
            if status == "Conforme":
                status = "Violação"

        resultados.append({
            "Motorista": row['Motorista'],
            "Data_Ref": f"{row['Dia']} ({row['Semana']})",
            "Status": status,
            "Violacoes_Criticas": violacoes_criticas,
            "Violacoes_Secundarias": violacoes_secundarias,
            "Tem_Critica": len(violacoes_criticas) > 0,
            "Jornada_Total": row['Jornada_Total'],
            "Interjornada": row['Interjornada'],
            "Conducao_Continua": row['Max_Conducao_Continua']
        })
        
    return pd.DataFrame(resultados)

# --- INTERFACE PRINCIPAL ---

# Tenta carregar imagens
try:
    st.sidebar.image("imgs/v-c.png", width=120)
except:
    pass

st.sidebar.markdown("# Auditoria de Jornada")
st.sidebar.info("Foco prioritário: Tempo de Condução Contínua (Máx 5h30).")

st.title("🚛 Auditoria de Jornada (Lei 13.103)")
st.markdown("""
Analise o relatório de jornada. 
**Prioridade Zero:** Identificar motoristas que ultrapassaram o tempo limite de direção ininterrupta (**5h30**).
""")

uploaded_file = st.file_uploader("Carregue o relatório `Jornada de Motorista` (Excel ou CSV)", type=['xlsx', 'csv'])

if uploaded_file:
    with st.status("A processar a inteligência de dados...", expanded=True) as status:
        st.write("Lendo estrutura do ficheiro...")
        df_flat = processar_relatorio_complexo(uploaded_file)
        
        if df_flat is not None and not df_flat.empty:
            st.write(f"Dados estruturados: {len(df_flat)} registos processados.")
            
            st.write("Verificando limites de 5h30 de condução...")
            df_analise = analisar_conformidade(df_flat)
            status.update(label="Análise Concluída!", state="complete", expanded=False)
            
            # --- SEPARAÇÃO DOS DADOS ---
            df_criticos = df_analise[df_analise['Tem_Critica'] == True]
            total_criticos = len(df_criticos)
            
            # --- KPIs GERAIS ---
            st.markdown("### 📊 Indicadores de Risco")
            col1, col2, col3, col4 = st.columns(4)
            
            col1.metric("Dias Analisados", len(df_analise))
            col2.metric("Motoristas Auditados", df_analise['Motorista'].nunique())
            
            # KPI DE DESTAQUE PARA CONDUÇÃO
            col3.metric(
                "Violações de Condução (>5h30)", 
                total_criticos, 
                delta="- Crítico" if total_criticos > 0 else "OK", 
                delta_color="inverse"
            )
            
            total_outras = df_analise['Violacoes_Secundarias'].apply(len).sum()
            col4.metric("Outras Violações (Interjornada)", total_outras, delta_color="inverse")

            st.markdown("---")

            # --- ABAS DE DETALHE ---
            tab1, tab2, tab3 = st.tabs(["🚨 PONTOS DE ATENÇÃO (Condução)", "📉 Outras Infrações", "📋 Dados Completos"])

            with tab1:
                st.subheader("🔴 Prioridade: Excesso de Condução Contínua")
                st.markdown("Estes eventos representam o maior risco de acidente e passivo trabalhista (Lei 13.103 - Art. 67-C).")
                
                if not df_criticos.empty:
                    # Ranking dos Críticos
                    ranking_critico = df_criticos['Motorista'].value_counts().reset_index()
                    ranking_critico.columns = ['Motorista', 'Ocorrências > 5h30']
                    
                    c1, c2 = st.columns([1, 2])
                    with c1:
                        st.markdown("**Top Infratores (Condução Contínua)**")
                        st.dataframe(ranking_critico, hide_index=True, use_container_width=True)
                    
                    with c2:
                        st.markdown("**Detalhamento das Ocorrências Críticas**")
                        motorista_foco = st.selectbox("Filtrar Motorista:", ["Todos"] + list(ranking_critico['Motorista']), key="sb_critico")
                        
                        df_show = df_criticos.copy()
                        if motorista_foco != "Todos":
                            df_show = df_show[df_show['Motorista'] == motorista_foco]
                        
                        for idx, row in df_show.iterrows():
                            # CARD VERMELHO PARA CRÍTICO
                            st.markdown(f"""
                            <div class="violation-card-critical">
                                <h4>👮 {row['Motorista']}</h4>
                                <strong>📅 Data: {row['Data_Ref']}</strong><br>
                                <span style="font-size: 1.2em;">⏱️ {row['Violacoes_Criticas'][0]}</span>
                            </div>
                            """, unsafe_allow_html=True)
                else:
                    st.success("✅ Excelente! Nenhum motorista excedeu o limite de 5h30 de condução contínua.")

            with tab2:
                st.subheader("🟠 Outras Infrações (Interjornada)")
                
                # Filtra quem tem violação secundária
                df_secundario = df_analise[df_analise['Violacoes_Secundarias'].apply(len) > 0]
                
                if not df_secundario.empty:
                    for idx, row in df_secundario.iterrows():
                        msg_list = "<br>".join([f"- {v}" for v in row['Violacoes_Secundarias']])
                        st.markdown(f"""
                        <div class="violation-card-warning">
                            <strong>{row['Motorista']} - {row['Data_Ref']}</strong><br>
                            {msg_list}
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.success("Nenhuma violação de interjornada encontrada.")

            with tab3:
                st.subheader("Tabela Analítica Completa")
                
                # Prepara dataframe para visualização limpa
                df_view = df_analise.copy()
                df_view['Infrações Condução'] = df_view['Violacoes_Criticas'].apply(lambda x: ", ".join(x) if x else "")
                df_view['Outras Infrações'] = df_view['Violacoes_Secundarias'].apply(lambda x: ", ".join(x) if x else "")
                
                st.dataframe(
                    df_view[['Motorista', 'Data_Ref', 'Status', 'Conducao_Continua', 'Infrações Condução', 'Interjornada', 'Outras Infrações']],
                    use_container_width=True
                )
                
                # Download CSV
                csv = df_view.to_csv(index=False).encode('utf-8')
                st.download_button("📥 Baixar Relatório Completo", data=csv, file_name="auditoria_conducao_lei13103.csv", mime="text/csv")

        else:
            st.error("Não foi possível ler os dados. Verifique se o formato do ficheiro corresponde ao padrão 'Jornada de Motorista'.")
