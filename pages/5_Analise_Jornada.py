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
    .violation-card {
        background-color: #ffe6e6;
        border-radius: 5px;
        padding: 10px;
        color: #b30000;
        margin-bottom: 5px;
        border: 1px solid #ffcccc;
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
    e transforma em uma tabela plana (flat table) para análise.
    """
    try:
        # Lê o arquivo bruto sem cabeçalho para varrer as linhas manualmente
        if file.name.endswith('.csv'):
            # Tenta diferentes encodings
            try:
                df_raw = pd.read_csv(file, header=None, encoding='utf-8', sep=',')
            except:
                df_raw = pd.read_csv(file, header=None, encoding='latin1', sep=',')
        else:
            df_raw = pd.read_excel(file, header=None)

        dados_processados = []
        motorista_atual = None
        
        # Itera linha a linha
        for index, row in df_raw.iterrows():
            row_list = [str(x).strip() for x in row.values]
            
            # Limpeza básica de 'nan' string
            row_list = [x if x.lower() != 'nan' else '' for x in row_list]

            # 1. Tenta identificar o Motorista 
            # Lógica: Coluna 1 (index 1) tem texto, Coluna 0 é vazia, e não é cabeçalho
            if len(row_list) > 2 and row_list[1] and row_list[1].lower() not in ['dia do mês', 'nome', '', 'jornada de motorista']:
                # Verifica se é um nome (não começa com número, coluna seguinte vazia)
                if not row_list[1][0].isdigit() and row_list[2] == '':
                    motorista_atual = row_list[1]
                    continue
            
            # 2. Identifica se é uma linha de dados de jornada
            # A linha de dados começa com o dia do mês (ex: "01") na coluna 1
            if len(row_list) > 13 and motorista_atual:
                dia_mes = row_list[1]
                
                # Verifica se a coluna "Dia do Mês" é um número válido (1-31)
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
        st.error(f"Erro ao processar estrutura do arquivo. Detalhe: {e}")
        return None

def analisar_conformidade(df):
    """Aplica as regras da Lei 13.103 (Exceto Refeição, conforme solicitado)."""
    resultados = []
    
    for idx, row in df.iterrows():
        violacoes = []
        status = "Conforme"
        
        # Converter tempos para minutos para cálculo
        interjornada_min = time_str_to_minutes(row['Interjornada'])
        conducao_continua_min = time_str_to_minutes(row['Max_Conducao_Continua'])
        # refeicao_min = time_str_to_minutes(row['Refeicao']) # Ignorado temporariamente
        # jornada_total_min = time_str_to_minutes(row['Jornada_Total']) # Ignorado temporariamente
        
        # --- REGRA 1: Interjornada (Mínimo 11h = 660 min) ---
        # Ignoramos se for 0, pois pode ser o primeiro dia ou folga
        if 0 < interjornada_min < 660: 
            # Tolerância de 10 min (considera violação se < 10h50m)
            if interjornada_min < 650:
                violacoes.append(f"Interjornada de {row['Interjornada']} (Mín exigido: 11:00)")
                status = "Violação"

        # --- REGRA 2: Condução Contínua (Máx 5h30 = 330 min) ---
        if conducao_continua_min > 330:
            violacoes.append(f"Dirigiu {row['Max_Conducao_Continua']} sem parar (Máx permitido: 05:30)")
            status = "Violação"

        # --- REGRA 3: Refeição (DESATIVADA TEMPORARIAMENTE) ---
        # if jornada_total_min > 360:
        #     if refeicao_min < 60:
        #         violacoes.append(f"Intervalo de refeição de {row['Refeicao']} (Mín exigido: 01:00)")
        #         status = "Violação"

        resultados.append({
            "Motorista": row['Motorista'],
            "Dia": row['Dia'],
            "Semana": row['Semana'],
            "Data_Ref": f"{row['Dia']} ({row['Semana']})",
            "Status": status,
            "Violacoes_Lista": violacoes,
            "Violacoes_Texto": ", ".join(violacoes) if violacoes else "Nenhuma",
            "Jornada_Total": row['Jornada_Total'],
            "Interjornada": row['Interjornada'],
            "Conducao_Continua": row['Max_Conducao_Continua'],
            "Refeicao": row['Refeicao']
        })
        
    return pd.DataFrame(resultados)

# --- INTERFACE PRINCIPAL ---

# Tenta carregar imagens, se falhar, segue sem elas
try:
    st.sidebar.image("imgs/v-c.png", width=120)
except:
    pass

st.sidebar.markdown("# Auditoria de Jornada")
st.sidebar.info("Ferramenta para análise automática de conformidade com a Lei do Motorista 13.103.")

st.title("🚛 Auditoria de Jornada (Lei 13.103)")
st.markdown("Analise o relatório de jornada, identifique não conformidades (**Interjornada e Condução Contínua**) e garanta a segurança jurídica da frota.")

uploaded_file = st.file_uploader("Carregue o relatório `Jornada de Motorista` (Excel ou CSV)", type=['xlsx', 'csv'])

if uploaded_file:
    with st.status("A processar a inteligência de dados...", expanded=True) as status:
        # 1. Processamento
        st.write("Lendo estrutura do arquivo...")
        df_flat = processar_relatorio_complexo(uploaded_file)
        
        if df_flat is not None and not df_flat.empty:
            st.write(f"Dados estruturados com sucesso: {len(df_flat)} registros de jornada encontrados.")
            
            # 2. Análise
            st.write("Aplicando regras da Lei 13.103 (Ignorando Refeição)...")
            df_analise = analisar_conformidade(df_flat)
            status.update(label="Análise Concluída!", state="complete", expanded=False)
            
            # --- KPIs GERAIS ---
            total_registros = len(df_analise)
            df_violacoes = df_analise[df_analise['Status'] == 'Violação']
            total_violacoes = len(df_violacoes)
            motoristas_com_infracao = df_violacoes['Motorista'].nunique()
            percentual_conformidade = ((total_registros - total_violacoes) / total_registros) * 100
            
            st.markdown("### 📊 Panorama Geral")
            col1, col2, col3, col4 = st.columns(4)
            
            col1.metric("Dias Analisados", total_registros)
            col2.metric("Motoristas com Infração", f"{motoristas_com_infracao} / {df_analise['Motorista'].nunique()}", delta_color="inverse")
            col3.metric("Total de Infrações", total_violacoes, delta_color="inverse")
            col4.metric("Índice de Conformidade", f"{percentual_conformidade:.1f}%", 
                        delta=f"{percentual_conformidade-100:.1f}%" if percentual_conformidade < 100 else "OK")

            st.markdown("---")

            # --- ABAS DE DETALHE ---
            tab1, tab2, tab3 = st.tabs(["🔴 Pontos de Atenção (Infrações)", "📈 Gráficos Gerenciais", "📋 Dados Completos"])

            with tab1:
                st.subheader("Detalhamento das Infrações Encontradas")
                
                if not df_violacoes.empty:
                    # Ranking de Infratores
                    ranking = df_violacoes['Motorista'].value_counts().reset_index()
                    ranking.columns = ['Motorista', 'Qtd Infrações']
                    
                    c1, c2 = st.columns([1, 2])
                    with c1:
                        st.markdown("**Top Infratores**")
                        st.dataframe(ranking, hide_index=True, use_container_width=True)
                    
                    with c2:
                        st.markdown("**Detalhes das Ocorrências**")
                        motorista_foco = st.selectbox("Filtrar por Motorista:", ["Todos"] + list(ranking['Motorista']))
                        
                        df_filtro = df_violacoes.copy()
                        if motorista_foco != "Todos":
                            df_filtro = df_filtro[df_filtro['Motorista'] == motorista_foco]
                        
                        for idx, row in df_filtro.iterrows():
                            with st.expander(f"👮 {row['Motorista']} | Dia {row['Data_Ref']} | {len(row['Violacoes_Lista'])} Infração(ões)", expanded=True):
                                for v in row['Violacoes_Lista']:
                                    st.markdown(f"- ❌ **{v}**")
                                st.caption(f"Jornada: {row['Jornada_Total']} | Refeição: {row['Refeicao']} | Interjornada: {row['Interjornada']}")
                else:
                    st.success("✅ Nenhuma violação de Interjornada ou Condução Contínua encontrada! Parabéns pela gestão.")

            with tab2:
                c1, c2 = st.columns(2)
                
                # Gráfico de Tipos de Violação
                violacoes_flat = []
                for v_list in df_analise['Violacoes_Lista']:
                    for v in v_list:
                        # Simplifica o nome da infração para o gráfico
                        if "Interjornada" in v: tipo = "Interjornada Insuficiente"
                        elif "condução contínua" in v: tipo = "Excesso Condução Contínua"
                        else: tipo = "Outros"
                        violacoes_flat.append(tipo)
                
                if violacoes_flat:
                    df_v_type = pd.DataFrame(violacoes_flat, columns=['Tipo']).value_counts().reset_index()
                    df_v_type.columns = ['Tipo', 'Qtd']
                    
                    fig_pizza = px.pie(df_v_type, values='Qtd', names='Tipo', title='Distribuição por Tipo de Infração', hole=0.4, color_discrete_sequence=px.colors.qualitative.Set1)
                    c1.plotly_chart(fig_pizza, use_container_width=True)
                
                # Gráfico Barras Infratores
                if not df_violacoes.empty:
                    ranking_top10 = ranking.head(10).sort_values('Qtd Infrações', ascending=True)
                    fig_bar = px.bar(ranking_top10, x='Qtd Infrações', y='Motorista', orientation='h', title='Top 10 Motoristas com Ocorrências', text='Qtd Infrações')
                    c2.plotly_chart(fig_bar, use_container_width=True)
                else:
                    c1.info("Sem dados para gráficos de infração.")

            with tab3:
                st.subheader("Tabela Analítica Completa")
                
                def highlight_status(val):
                    color = '#ffe6e6' if val == 'Violação' else '#e6ffe6'
                    return f'background-color: {color}'

                st.dataframe(
                    df_analise.style.applymap(highlight_status, subset=['Status']),
                    use_container_width=True,
                    column_config={
                        "Violacoes_Texto": st.column_config.TextColumn("Detalhes da Infração", width="large"),
                        "Violacoes_Lista": None # Ocultar coluna de lista
                    }
                )
                
                # Prepara CSV para download (converte lista para string)
                df_download = df_analise.drop(columns=['Violacoes_Lista'])
                csv = df_download.to_csv(index=False).encode('utf-8')
                st.download_button("📥 Baixar Relatório de Auditoria (CSV)", data=csv, file_name="auditoria_lei_motorista.csv", mime="text/csv")

        else:
            st.error("Não foi possível ler os dados corretamente. Verifique se o formato do arquivo corresponde ao padrão 'Jornada de Motorista' (Nome do motorista nas linhas e dados abaixo).")
