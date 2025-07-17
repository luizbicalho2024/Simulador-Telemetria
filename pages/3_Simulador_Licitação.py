# pages/3_Simulador_Licitação.py
from decimal import Decimal, ROUND_DOWN, ROUND_HALF_UP
import pandas as pd
import streamlit as st
from datetime import datetime
import user_management_db as umdb
from logger_config import log
from config import PRECO_CUSTO_LICITACAO, AMORTIZACAO_HARDWARE_MESES # Importa do config

# --- 1. CONFIGURAÇÃO E AUTENTICAÇÃO ---
st.set_page_config(layout="wide", page_title="Simulador Licitações", page_icon="imgs/v-c.png")

if not st.session_state.get("authentication_status"):
    st.error("🔒 Acesso Negado! Por favor, faça login.")
    st.stop()

# --- 2. INTERFACE ---
try:
    st.image("imgs/logo.png", width=250)
except:
    pass

st.markdown("<h1 ...>Simulador para Licitações e Editais</h1>", ...)
# ... (cabeçalho da página como antes) ...

# --- Botão de Limpar Campos ---
if st.sidebar.button("🧹 Limpar Campos", use_container_width=True):
    # Limpa as chaves da sessão específicas deste simulador
    for key in st.session_state.keys():
        if key.startswith("licit_"):
            del st.session_state[key]
    st.toast("Campos do simulador de licitação foram limpos!", icon="✨")
    st.rerun()

st.sidebar.header("📝 Configurações da Licitação")
qtd = Decimal(st.sidebar.number_input("Qtd. de Veículos 🚗", ..., key="licit_qtd"))
# ... (outros inputs da sidebar, todos com a chave prefixada "licit_") ...

# --- 3. CÁLCULOS E EXIBIÇÃO ---
# ... (lógica de cálculo como antes, mas usando as constantes do config.py) ...
# ... (Exemplo: custo_hw_item = PRECO_CUSTO_LICITACAO[item]) ...

if proposta:
    # ... (exibição da tabela como antes) ...
    
    # --- NOVO: Botão para Guardar e Registar Proposta ---
    if st.button("💾 Registar Proposta no Histórico"):
        proposal_data = {
            "tipo": "Licitação",
            "empresa": f"Licitação {datetime.now().strftime('%Y-%m-%d')}", # Placeholder
            "consultor": st.session_state.get('name', 'N/A'),
            "valor_total": float(valor_global),
            "data_geracao": datetime.now()
        }
        if umdb.log_proposal(proposal_data):
            st.toast("Proposta registada com sucesso no dashboard!", icon="📊")
        else:
            st.error("Falha ao registar proposta.")
