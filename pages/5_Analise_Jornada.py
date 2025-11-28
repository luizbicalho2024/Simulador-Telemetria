# pages/🚛_Analise_Jornada.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
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
    .violation-card {
        background-color: #ffe6e6;
        border-radius: 5px;
        padding: 10px;
        color: #b30000;
        margin-bottom: 5px;
    }
    </style>
""", unsafe_allow_html=True)

if not st.session_state.get("authentication_status"):
    st.error("🔒 Acesso Negado! Por favor, faça login.")
    st.stop()

# --- FUNÇÕES DE PROCESSAMENTO ---

def time_str_to_minutes(time_str):
    """Converte string 'HH:MM:SS' para minutos totais."""
    if pd.isna(time_str) or str(time_str).strip() == '':
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
    e transforma em uma tabela plana (flat table) para análise.
    """
    try:
        # Lê o arquivo bruto sem cabeçalho para varrer as linhas
        if file.name.endswith('.csv'):
            df_raw = pd.read_csv(file, header=None, encoding='latin1', sep=',') # Tenta latin1 ou utf-8
        else:
            df_raw = pd.read_excel(file, header=None)

        dados_processados = []
        motorista_atual = None
        matricula_atual = None
        
        # Itera linha a linha
        for index, row in df_raw.iterrows():
            row_list = [str(x).strip() for x in row.values]
            
            # 1. Tenta identificar o Motorista (Lógica: Coluna 1 vazia, Coluna 2 tem nome, resto vazio ou NaN)
            # Baseado no seu arquivo: ",Nome,,,,,"
            if len(row_list) > 2 and row_list[1] and row_list[1].lower() not in ['nan', 'dia do mês', 'nome', ''] and row_list[2] == 'nan':
                # Verifica se é uma linha de nome (não contém números ou datas óbvias)
                if not any(char.isdigit() for char in row_list[1]):
                    motorista_atual = row_list[1]
                    continue
            
            # 2. Tenta Identificar Matrícula (Opcional, aparece abaixo do nome)
            if len(row_list) > 2 and row_list[1] and row_list[1].isdigit():
                matricula_atual = row_list[1]
                continue

            # 3. Identifica se é a linha de Cabeçalho dos dados
            if len(row_list) > 2 and "Dia do Mês" in str(row_list[1]):
                continue # Pula o cabeçalho, já sabemos a ordem

            # 4. Identifica se é uma linha de dados
            # A linha de dados começa com o dia do mês (ex: "01") na coluna 1
            if len(row_list) > 10 and motorista_atual:
                dia_mes = row_list[1]
                # Verifica se a primeira coluna é um número (dia)
                if dia_mes.isdigit() and int(dia_mes) <= 31:
                    # Mapeamento baseado no seu CSV
                    dados_processados.append({
                        "Motorista": motorista_atual,
                        "Matricula": matricula_atual,
                        "Data": f"{row_list[1]} ({row_list[2]})", # Dia + Semana
                        "Inicio_Jornada": row_list[3],
                        "Fim_Jornada": row_list[4],
                        "Jornada_Total": row_list[5],
                        "Conducao_Total": row_list[6],
                        "Max_Conducao_Continua": row_list[9], # Verifiquei posição no seu csv
                        "Espera": row_list[10],
                        "Refeicao": row_list[11],
                        "Descanso": row_list[12],
                        "Interjornada": row_list[13]
                    })

        return pd.DataFrame(dados_processados)

    except Exception as e:
        st.error(f"Erro ao processar estrutura do arquivo: {e}")
        return None

def analisar_conformidade(df):
    """Aplica as regras da Lei 13.103."""
    resultados = []
    
    for idx, row in df.iterrows():
        violacoes = []
        status = "Conforme"
        
        # Converter tempos para minutos
        interjornada_min = time_str_to_minutes(row['Interjornada'])
        conducao_continua_min = time_str_to_minutes(row['Max_Conducao_Continua'])
        refeicao_min = time_str_to_minutes(row['Refeicao'])
        jornada_total_min = time_str_to_minutes(row['Jornada_Total'])
        
        # --- REGRA 1: Interjornada (Mínimo 11h = 660 min) ---
        # Obs: Algumas convenções permitem fracionar 8+3, aqui validamos o total
        if interjornada_min < 660 and interjornada_min > 0: # > 0 para ignorar dias sem registro anterior
            violacoes.append(f"Interjornada insuficiente: {row['Interjornada']} (Mín: 11:00)")
            status = "Violação"

        # --- REGRA 2: Condução Contínua (Máx 5h30 = 330 min) ---
        if conducao_continua_min > 330:
            violacoes.append(f"Excesso condução contínua: {row['Max_Conducao_Continua']} (Máx: 05:30)")
            status = "Violação"

        # --- REGRA 3: Refeição (Mín 1h para jornadas > 6h) ---
        if jornada_total_min > 360 and refeicao_min < 60:
            violacoes.append(f"Intervalo refeição curto: {row['Refeicao']} (Mín: 01:00)")
            status = "Violação"

        resultados.append({
            "Motorista": row['Motorista'],
            "Data": row['Data'],
            "Status": status,
            "Violacoes": ", ".join(violacoes),
            "Qtd_Violacoes": len(violacoes),
            "Jornada_Total": row['Jornada_Total'],
            "Interjornada": row['Interjornada'],
            "Conducao_Continua": row['Max_Conducao_Continua']
        })
        
    return pd.DataFrame(resultados)

# --- INTERFACE PRINCIPAL ---

st.title("🚛 Auditoria de Jornada (Lei 13.103)")
st.markdown("Analise o relatório de jornada, identifique não conformidades e garanta a segurança jurídica da frota.")

uploaded_file = st.file_uploader("Carregue o relatório `Jornada de Motorista` (Excel ou CSV)", type=['xlsx', 'csv'])

if uploaded_file:
    with st.spinner("A processar a inteligência de dados..."):
        # 1. Processamento
        df_flat = processar_relatorio_complexo(uploaded_file)
        
        if df_flat is not None and not df_flat.empty:
            # 2. Análise
            df_analise = analisar_conformidade(df_flat)
            
            # --- KPIs GERAIS ---
            total_registros = len(df_analise)
            total_violacoes = df_analise[df_analise['Status'] == 'Violação'].shape[0]
            percentual_conformidade = ((total_registros - total_violacoes) / total_registros) * 100
            
            st.markdown("### 📊 Panorama Geral")
            col1, col2, col3, col4 = st.columns(4)
            
            col1.metric("Dias Analisados", total_registros)
            col2.metric("Motoristas", df_analise['Motorista'].nunique())
            col3.metric("Ocorrências de Violação", total_violacoes, delta_color="inverse")
            col4.metric("Índice de Conformidade", f"{percentual_conformidade:.1f}%", 
                        delta=f"{percentual_conformidade-100:.1f}%" if percentual_conformidade < 100 else "OK")

            st.markdown("---")

            # --- ABAS DE DETALHE ---
            tab1, tab2, tab3 = st.tabs(["🔴 Pontos de Atenção", "📈 Gráficos Gerenciais", "📋 Dados Completos"])

            with tab1:
                st.subheader("Motoristas com Maiores Índices de Risco")
                
                # Ranking de Infratores
                ranking = df_analise[df_analise['Status'] == 'Violação']['Motorista'].value_counts().reset_index()
                ranking.columns = ['Motorista', 'Qtd Violações']
                
                c1, c2 = st.columns([1, 2])
                with c1:
                    st.dataframe(ranking, hide_index=True, use_container_width=True)
                
                with c2:
                    if not ranking.empty:
                        motorista_foco = st.selectbox("Filtrar detalhes por Motorista:", ["Todos"] + list(ranking['Motorista']))
                        
                        df_filtro = df_analise[df_analise['Status'] == 'Violação']
                        if motorista_foco != "Todos":
                            df_filtro = df_filtro[df_filtro['Motorista'] == motorista_foco]
                        
                        for idx, row in df_filtro.iterrows():
                            st.markdown(f"""
                            <div class="violation-card">
                                <strong>👮 {row['Motorista']} - {row['Data']}</strong><br>
                                <small>{row['Violacoes']}</small>
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.success("Nenhuma violação encontrada! Parabéns pela gestão.")

            with tab2:
                c1, c2 = st.columns(2)
                
                # Gráfico de Tipos de Violação
                violacoes_list = []
                for v in df_analise['Violacoes']:
                    if v:
                        parts = v.split(', ')
                        for p in parts:
                            base_violation = p.split(':')[0]
                            violacoes_list.append(base_violation)
                
                if violacoes_list:
                    df_v_type = pd.DataFrame(violacoes_list, columns=['Tipo']).value_counts().reset_index()
                    df_v_type.columns = ['Tipo', 'Qtd']
                    
                    fig_pizza = px.pie(df_v_type, values='Qtd', names='Tipo', title='Distribuição por Tipo de Infração', hole=0.4)
                    c1.plotly_chart(fig_pizza, use_container_width=True)
                
                # Gráfico Evolução (Se houvesse data real parseada, aqui faremos por motorista)
                fig_bar = px.bar(ranking.head(10), x='Qtd Violações', y='Motorista', orientation='h', title='Top 10 Motoristas com Ocorrências')
                c2.plotly_chart(fig_bar, use_container_width=True)

            with tab3:
                st.subheader("Tabela Analítica Completa")
                
                def highlight_status(val):
                    color = '#ffe6e6' if val == 'Violação' else '#e6ffe6'
                    return f'background-color: {color}'

                st.dataframe(
                    df_analise.style.applymap(highlight_status, subset=['Status']),
                    use_container_width=True,
                    column_config={
                        "Violacoes": st.column_config.TextColumn("Detalhes da Infração", width="medium"),
                    }
                )
                
                csv = df_analise.to_csv(index=False).encode('utf-8')
                st.download_button("📥 Baixar Relatório de Auditoria", data=csv, file_name="auditoria_lei_motorista.csv", mime="text/csv")

        else:
            st.warning("Não foi possível ler os dados. Verifique se o formato do arquivo corresponde ao padrão 'Jornada de Motorista'.")
