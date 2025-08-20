# pages/🔗_Vinculo_Clientes_Terminais.py
import streamlit as st
import pandas as pd
import user_management_db as umdb

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

# --- 4. ANÁLISE E EXIBIÇÃO DAS COLUNAS ---
if uploaded_clientes and uploaded_rastreadores:
    try:
        st.subheader("Colunas Encontradas nos Ficheiros")
        
        # Lê e exibe as colunas do relatório de clientes
        with st.spinner("A ler o relatório de clientes..."):
            df_clientes = pd.read_excel(uploaded_clientes, header=11, engine='openpyxl')
            st.markdown("#### Colunas do `relatorio_clientes.xlsx`:")
            st.write(df_clientes.columns.tolist())

        # Lê e exibe as colunas do relatório de rastreadores
        with st.spinner("A ler o relatório de rastreadores..."):
            df_rastreadores = pd.read_excel(uploaded_rastreadores, header=11, engine='openpyxl')
            st.markdown("#### Colunas do `relatorio_rastreador.xlsx`:")
            st.write(df_rastreadores.columns.tolist())

    except Exception as e:
        st.error(f"Ocorreu um erro ao ler os ficheiros: {e}")
        st.info("Por favor, verifique se os ficheiros não estão corrompidos e se o cabeçalho de ambos está na linha 12.")
else:
    st.info("Por favor, carregue ambos os ficheiros para iniciar o diagnóstico.")
