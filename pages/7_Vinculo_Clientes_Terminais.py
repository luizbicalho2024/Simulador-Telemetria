# pages/🔗_Vinculo_Clientes_Terminais.py
import streamlit as st
import pandas as pd
import user_management_db as umdb
import json

# --- 1. CONFIGURAÇÃO E AUTENTICAÇÃO ---
st.set_page_config(
    layout="wide",
    page_title="Diagnóstico de Vínculos",
    page_icon="🔗"
)

if not st.session_state.get("authentication_status"):
    st.error("🔒 Acesso Negado! Por favor, faça login para visualizar esta página.")
    st.stop()

# --- 2. INTERFACE DA PÁGINA ---
st.sidebar.image("imgs/v-c.png", width=120)
st.sidebar.title(f"Olá, {st.session_state.get('name', 'N/A')}! 👋")
st.sidebar.markdown("---")

try:
    st.image("imgs/logo.png", width=250)
except: pass

st.markdown("<h1 style='text-align: center; color: #006494;'>🔗 Diagnóstico de Vínculos de Clientes e Terminais</h1>", unsafe_allow_html=True)
st.markdown("---")

# --- 3. UPLOAD DOS FICHEIROS ---
st.subheader("Carregamento dos Relatórios para Diagnóstico")
col1, col2 = st.columns(2)

with col1:
    st.info("**1. Relatório de Clientes**")
    uploaded_clientes = st.file_uploader(
        "Carregue o `relatorio_clientes.xlsx`",
        type=['xlsx']
    )

with col2:
    st.info("**2. Relatório de Rastreadores (Estoque)**")
    uploaded_rastreadores = st.file_uploader(
        "Carregue o `relatorio_rastreador.xlsx`",
        type=['xlsx']
    )

st.markdown("---")

# --- 4. ANÁLISE E EXIBIÇÃO EM JSON ---
if uploaded_clientes and uploaded_rastreadores:
    try:
        st.subheader("Dados Extraídos das Planilhas (Formato JSON)")
        
        # Lê e exibe o JSON do relatório de clientes
        with st.expander("Dados do `relatorio_clientes.xlsx`", expanded=True):
            st.markdown("Abaixo estão os dados lidos da sua planilha de clientes. Isto ajuda-nos a ver a estrutura aninhada.")
            # Lê a partir da linha 12 (header=11)
            df_clientes = pd.read_excel(uploaded_clientes, header=11, engine='openpyxl')
            # Converte para JSON, tratando valores NaN (Not a Number) para null
            json_clientes = json.loads(df_clientes.to_json(orient='records', indent=4, default_handler=str))
            st.json(json_clientes)

        # Lê e exibe o JSON do relatório de rastreadores
        with st.expander("Dados do `relatorio_rastreador.xlsx`", expanded=True):
            st.markdown("Abaixo estão os dados lidos da sua planilha de rastreadores.")
            df_rastreadores = pd.read_excel(uploaded_rastreadores, header=11, engine='openpyxl')
            # Converte para JSON, tratando valores NaN (Not a Number) para null
            json_rastreadores = json.loads(df_rastreadores.to_json(orient='records', indent=4, default_handler=str))
            st.json(json_rastreadores)

    except Exception as e:
        st.error(f"Ocorreu um erro ao ler os ficheiros: {e}")
        st.info("Por favor, verifique se os ficheiros não estão corrompidos e se o cabeçalho de ambos está na linha 12.")
else:
    st.info("Por favor, carregue ambos os ficheiros para iniciar o diagnóstico.")
