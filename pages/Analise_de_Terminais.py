# pages/Analise_de_Terminais.py
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# --- 1. CONFIGURAÇÃO E AUTENTICAÇÃO ---
st.set_page_config(
    layout="wide",
    page_title="Análise de Terminais",
    page_icon="📡"
)

if not st.session_state.get("authentication_status"):
    st.error("🔒 Acesso Negado! Por favor, faça login para visualizar esta página.")
    st.stop()

# --- 2. FUNÇÕES AUXILIARES ---
@st.cache_data
def processar_planilha_terminais(uploaded_file):
    """
    Lê a planilha de terminais, extrai o nome do cliente e os dados,
    e realiza a análise de status.
    """
    # Lê a linha 9 para obter o nome do cliente
    # skiprows=8 lê a partir da 9ª linha, nrows=1 pega apenas essa linha
    df_cliente = pd.read_excel(uploaded_file, header=None, skiprows=8, nrows=1, engine='openpyxl')
    # O nome do cliente estará na primeira célula (índice 0)
    nome_cliente = df_cliente.iloc[0, 0] if not df_cliente.empty else "Cliente não identificado"

    # Lê a tabela de dados a partir da linha 12 (índice 11)
    df_terminais = pd.read_excel(uploaded_file, header=11, engine='openpyxl')

    # Validação de colunas essenciais
    required_cols = ['Terminal', 'Placa', 'Rastreador', 'Modelo', 'Data Transmissão']
    if not all(col in df_terminais.columns for col in required_cols):
        raise ValueError(f"O ficheiro não contém todas as colunas necessárias. Verifique se existem as colunas: {', '.join(required_cols)}")

    # Limpeza e processamento dos dados
    df_terminais.dropna(subset=['Terminal'], inplace=True) # Remove linhas vazias
    df_terminais['Data Transmissão'] = pd.to_datetime(df_terminais['Data Transmissão'], errors='coerce')
    df_terminais.dropna(subset=['Data Transmissão'], inplace=True) # Remove linhas com datas inválidas

    # Análise de status
    dez_dias_atras = datetime.now() - timedelta(days=10)
    df_terminais['Status_Atualizacao'] = df_terminais['Data Transmissão'].apply(
        lambda data: "Atualizado" if data >= dez_dias_atras else "Desatualizado"
    )
    
    return nome_cliente, df_terminais

# --- 3. INTERFACE DA PÁGINA ---
st.sidebar.image("imgs/v-c.png", width=120)
st.sidebar.title(f"Olá, {st.session_state.get('name', 'N/A')}! 👋")
st.sidebar.markdown("---")

try:
    st.image("imgs/logo.png", width=250)
except: pass

st.markdown("<h1 style='text-align: center; color: #006494;'>📡 Análise de Status de Terminais</h1>", unsafe_allow_html=True)
st.markdown("---")

# --- 4. UPLOAD DO FICHEIRO ---
st.subheader("Carregamento do Relatório")
st.info("Por favor, carregue o ficheiro `lista_de_terminais.xlsx` exportado do sistema.")

uploaded_file = st.file_uploader(
    "Selecione o relatório de terminais",
    type=['xlsx']
)

st.markdown("---")

# --- 5. ANÁLISE E EXIBIÇÃO ---
if uploaded_file:
    try:
        nome_cliente, df_analise = processar_planilha_terminais(uploaded_file)
        
        st.header(f"Cliente: {nome_cliente}")
        
        # Filtra os dataframes por status
        df_atualizados = df_analise[df_analise['Status_Atualizacao'] == 'Atualizado']
        df_desatualizados = df_analise[df_analise['Status_Atualizacao'] == 'Desatualizado']
        
        # --- CARDS DE MÉTRICAS ---
        col1, col2 = st.columns(2)
        col1.metric(
            label="✅ Total de Terminais Atualizados",
            value=len(df_atualizados),
            help="Terminais que transmitiram nos últimos 10 dias."
        )
        col2.metric(
            label="⚠️ Total de Terminais Desatualizados",
            value=len(df_desatualizados),
            help="Terminais que não transmitem há mais de 10 dias."
        )

        st.markdown("---")
        
        # --- TABELA DE TERMINAIS DESATUALIZADOS ---
        st.subheader("Lista de Terminais Desatualizados")
        if not df_desatualizados.empty:
            st.warning("Atenção: Os terminais abaixo precisam de verificação.")
            st.dataframe(
                df_desatualizados[['Terminal', 'Placa', 'Rastreador', 'Modelo', 'Data Transmissão']],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Data Transmissão": st.column_config.DatetimeColumn(
                        "Data da Última Transmissão",
                        format="DD/MM/YYYY HH:mm:ss"
                    )
                }
            )
        else:
            st.success("🎉 Excelente! Todos os terminais estão atualizados.")

    except Exception as e:
        st.error(f"Ocorreu um erro ao processar o ficheiro: {e}")
        st.info("Por favor, verifique se o ficheiro tem o formato e as colunas esperadas.")

else:
    st.info("Aguardando o carregamento de um ficheiro para iniciar a análise.")
