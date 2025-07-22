# pages/Dados_Clientes_PF_PJ.py
import streamlit as st
import pandas as pd
import io
import re
import user_management_db as umdb

# --- FUNÇÕES DE APOIO (LÓGICA DE PROCESSAMENTO) ---
# ... (as suas funções is_valid_email, processar_planilha_final, e to_excel permanecem aqui, sem alterações)

# --- 1. CONFIGURAÇÃO E AUTENTICAÇÃO ---
st.set_page_config(layout="wide", page_title="Organizador de Planilhas", page_icon="imgs/v-c.png")
if not st.session_state.get("authentication_status"):
    st.error("🔒 Acesso Negado! Por favor, faça login."); st.stop()

# --- 2. INTERFACE ---
st.sidebar.image("imgs/v-c.png", width=120)
try:
    st.image("imgs/logo.png", width=250)
except: pass

st.markdown("<h1 style='text-align: center; color: #54A033;'>Organizador de Planilhas de Clientes</h1>", unsafe_allow_html=True)
st.markdown("---")
st.write(f"Usuário: {st.session_state.get('name', 'N/A')} ({st.session_state.get('username', 'N/A')})")
st.write(f"Nível de Acesso: {st.session_state.get('role', 'Indefinido').capitalize()}")
st.markdown("---")

# --- 3. CONTEÚDO PRINCIPAL ---
st.write(
    "Faça o upload da sua planilha. A aplicação irá ler os dados a partir da linha 11, agrupar, validar e-mails e organizar as colunas."
)
uploaded_file = st.file_uploader(
    "Selecione o arquivo da planilha", type=['xlsx', 'csv'], accept_multiple_files=False
)

if uploaded_file:
    final_df = processar_planilha_final(uploaded_file)
    
    if final_df is not None and not final_df.empty:
        st.toast("Processamento concluído com sucesso!", icon="✅")
        st.dataframe(final_df.fillna(''))
        
        # Regista a ação de sucesso no log
        umdb.add_log(st.session_state["username"], "Processou Planilha", f"Ficheiro: {uploaded_file.name}, Linhas processadas: {len(final_df)}")
        
        st.download_button(
            label="📥 Baixar Planilha Final (.xlsx)",
            data=to_excel(final_df),
            file_name='relatorio_clientes_final.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    else:
        st.error("O processamento falhou ou não encontrou dados válidos.")
else:
    st.info("Aguardando o upload de um arquivo...")
