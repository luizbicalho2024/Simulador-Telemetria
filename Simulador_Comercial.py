# Simulador_Comercial.py
import streamlit as st
import pandas as pd
import user_management_db as umdb
import streamlit_authenticator as stauth

# --- 1. CONFIGURAÇÃO INICIAL DA PÁGINA ---
st.set_page_config(
    page_title="Simulador Telemetria",
    layout="wide",
    page_icon="imgs/v-c.png"
)

try:
    st.image("imgs/logo.png", width=250)
except Exception:
    pass

# --- 2. VERIFICAÇÃO DA CONEXÃO ---
if not umdb.get_mongo_client():
    st.error("🚨 FALHA CRÍTICA NA CONEXÃO COM A BASE DE DADOS.")
    st.stop()

# --- 3. CONFIGURAÇÃO DO AUTENTICADOR ---
credentials = umdb.fetch_all_users_for_auth()
authenticator = stauth.Authenticate(
    credentials, st.secrets["AUTH_COOKIE_NAME"], st.secrets["AUTH_COOKIE_KEY"],
    cookie_expiry_days=st.secrets.get("AUTH_COOKIE_EXPIRY_DAYS", 30), preauthorized=None
)

# --- 4. LÓGICA PRINCIPAL ---

# A. Criação do primeiro admin
if not credentials.get("usernames"):
    st.title("🚀 Bem-vindo ao Simulador de Telemetria!")
    st.subheader("Configuração Inicial: Crie a sua Conta de Administrador")
    with st.form("form_criar_primeiro_admin"):
        name = st.text_input("Nome Completo")
        username = st.text_input("Nome de Utilizador (login)")
        email = st.text_input("Email")
        password = st.text_input("Senha", type="password")
        if st.form_submit_button("✨ Criar Administrador"):
            if all([name, username, email, password]):
                if umdb.add_user(username, name, email, password, "admin"):
                    st.toast("Conta de administrador criada! A página será recarregada.", icon="🎉")
                    st.rerun()
            else:
                st.warning("Por favor, preencha todos os campos.")
    st.stop()

# B. Processo de Login
authenticator.login(location='main')

if st.session_state["authentication_status"]:
    # --- PÓS-LOGIN ---
    name = st.session_state["name"]
    username = st.session_state["username"]
    st.session_state.role = umdb.get_user_role(username)

    st.sidebar.image("imgs/v-c.png", width=120)
    st.sidebar.title(f"Olá, {name}! 👋")
    authenticator.logout("Sair", "sidebar")
    st.sidebar.markdown("---")

    if st.session_state.role == "user":
        with st.sidebar.expander("Minha Conta"):
            with st.form("form_alterar_senha_user", clear_on_submit=True):
                # ... (formulário de alteração de senha como antes)
                pass

    st.header("Página Principal")
    st.write("Navegue pelas ferramentas no menu lateral.")

    if st.session_state.role == "admin":
        st.markdown("---")
        st.subheader("Painel de Administração")
        tab_ver, tab_cad, tab_edit, tab_del, tab_precos = st.tabs([
            "👁️ Utilizadores", "➕ Cadastrar", "✏️ Editar", "🗑️ Excluir", "⚙️ Gerir Preços"
        ])
        
        # ... (abas de gestão de utilizadores como antes) ...

        with tab_precos:
            st.subheader("Gestão de Preços e Taxas da Plataforma")
            pricing_config = umdb.get_pricing_config()
            with st.form("form_edit_prices"):
                with st.expander("Simulador Pessoa Física (PF)", expanded=True):
                    pf_prices = pricing_config.get("PRECOS_PF", {})
                    col1, col2 = st.columns(2)
                    pf_prices["GPRS / Gsm"] = col1.number_input("Preço Rastreador GPRS/GSM (PF)", value=float(pf_prices.get("GPRS / Gsm", 0.0)), format="%.2f", key="pf_price_gprs")
                    pf_prices["Satelital"] = col2.number_input("Preço Rastreador Satelital (PF)", value=float(pf_prices.get("Satelital", 0.0)), format="%.2f", key="pf_price_sat")
                
                # Adicione expanders para os outros simuladores aqui (PJ, Licitação)
                
                if st.form_submit_button("✅ Salvar Todas as Alterações de Preços"):
                    new_config_data = umdb.get_pricing_config()
                    new_config_data["PRECOS_PF"] = pf_prices
                    # ... (atualize os outros dicionários) ...
                    
                    if umdb.update_pricing_config(new_config_data):
                        st.toast("Preços atualizados com sucesso!", icon="🎉")
                    else:
                        st.error("Falha ao atualizar os preços.")

elif st.session_state["authentication_status"] is False:
    st.error('❌ Nome de utilizador ou senha incorreto(s).')
elif st.session_state["authentication_status"] is None:
    st.title("Simulador de Telemetria")
    st.info('👋 Por favor, insira o seu nome de utilizador e senha para aceder.')
