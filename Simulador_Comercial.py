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
    st.info("Verifique os 'Secrets' e as permissões de IP no MongoDB Atlas.")
    st.stop()

# --- 3. CONFIGURAÇÃO DO AUTENTICADOR ---
credentials = umdb.fetch_all_users_for_auth()
authenticator = stauth.Authenticate(
    credentials,
    st.secrets["AUTH_COOKIE_NAME"],
    st.secrets["AUTH_COOKIE_KEY"],
    cookie_expiry_days=st.secrets.get("AUTH_COOKIE_EXPIRY_DAYS", 30),
    preauthorized=None
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
                    umdb.add_log(username, "Criação de Conta", "Primeiro administrador criado.")
                    st.toast("Conta de administrador criada! A página será recarregada.", icon="🎉")
                    st.rerun()
            else:
                st.warning("Por favor, preencha todos os campos.")
    st.stop()

# B. Processo de Login
authenticator.login(location='main')

# Regista o evento de login apenas uma vez por sessão
if "logged_in_log" not in st.session_state:
    st.session_state.logged_in_log = False
if st.session_state["authentication_status"] and not st.session_state.logged_in_log:
    umdb.add_log(st.session_state["username"], "Login bem-sucedido")
    st.session_state.logged_in_log = True
elif not st.session_state["authentication_status"]:
    st.session_state.logged_in_log = False


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
                current_pwd = st.text_input("Senha Atual", type="password", key="user_curr_pwd")
                new_pwd = st.text_input("Nova Senha", type="password", key="user_new_pwd")
                if st.form_submit_button("Salvar Nova Senha"):
                    user_hash = credentials["usernames"][username]["password"]
                    if umdb.verify_password(current_pwd, user_hash):
                        if umdb.update_user_password(username, new_pwd):
                            umdb.add_log(username, "Alterou a própria senha")
                            st.toast("Senha alterada com sucesso!", icon="✅")
                        else:
                            st.error("Ocorreu um erro ao alterar a senha.")
                    else:
                        st.error("A sua senha atual está incorreta.")

    st.header("Página Principal")
    st.write("Navegue pelas ferramentas no menu lateral.")

    if st.session_state.role == "admin":
        st.markdown("---")
        st.subheader("Painel de Administração")
        
        tab_ver, tab_cad, tab_edit, tab_del, tab_precos = st.tabs([
            "👁️ Utilizadores", "➕ Cadastrar", "✏️ Editar", "🗑️ Excluir", "⚙️ Gerir Preços"
        ])

        with tab_ver:
            st.dataframe(umdb.get_all_users_for_admin_display(), use_container_width=True, hide_index=True)

        with tab_cad:
            with st.form("form_cadastrar", clear_on_submit=True):
                st.subheader("Cadastrar Novo Utilizador")
                uname = st.text_input("Nome de Utilizador")
                nome_completo = st.text_input("Nome Completo")
                mail = st.text_input("Email")
                pwd = st.text_input("Senha", type="password")
                role = st.selectbox("Papel", ["user", "admin"], format_func=str.capitalize)
                if st.form_submit_button("Cadastrar Utilizador"):
                    if all([uname, nome_completo, mail, pwd, role]):
                        if umdb.add_user(uname, nome_completo, mail, pwd, role):
                            umdb.add_log(username, "Criou Utilizador", f"Novo utilizador: {uname}, Papel: {role}")
                            st.toast(f"Utilizador '{uname}' criado.", icon="➕")
                            st.rerun()
                    else:
                        st.warning("Preencha todos os campos.")

        users_dict = {u['username']: u for u in umdb.get_all_users_for_admin_display()}
        if users_dict:
            user_to_manage = st.selectbox("Selecione um utilizador para Editar ou Excluir:", list(users_dict.keys()), key="user_select_manage")
            user_data = users_dict.get(user_to_manage, {})

            with tab_edit:
                st.subheader(f"A editar: {user_to_manage}")
                with st.form(f"form_edit_{user_to_manage}"):
                    new_name = st.text_input("Nome Completo", value=user_data.get('name', ''))
                    new_email = st.text_input("Email", value=user_data.get('email', ''))
                    role_idx = ["user", "admin"].index(user_data.get('role', 'user'))
                    new_role = st.selectbox("Papel", ["user", "admin"], index=role_idx, format_func=str.capitalize)
                    if st.form_submit_button("Salvar Alterações"):
                        if umdb.update_user_details(user_to_manage, new_name, new_email, new_role):
                            umdb.add_log(username, "Editou Utilizador", f"Utilizador editado: {user_to_manage}")
                            st.toast("Detalhes atualizados.", icon="✏️")
                            st.rerun()

            with tab_del:
                st.subheader(f"Excluir: {user_to_manage}")
                st.warning(f"⚠️ Atenção: esta ação é irreversível.")
                if st.button(f"Excluir Permanentemente '{user_to_manage}'", type="primary"):
                    if umdb.delete_user(user_to_manage):
                        umdb.add_log(username, "Excluiu Utilizador", f"Utilizador excluído: {user_to_manage}")
                        st.toast(f"Utilizador '{user_to_manage}' excluído.", icon="🗑️")
                        st.rerun()
        else:
            with tab_edit: st.info("Nenhum utilizador para editar.")
            with tab_del: st.info("Nenhum utilizador para excluir.")

        with tab_precos:
            st.subheader("Gestão de Preços e Taxas da Plataforma")
            pricing_config = umdb.get_pricing_config()
            with st.form("form_edit_prices"):
                with st.expander("Simulador Pessoa Física (PF)", expanded=True):
                    pf_prices = pricing_config.get("PRECOS_PF", {})
                    col1, col2 = st.columns(2)
                    pf_prices["GPRS / Gsm"] = col1.number_input("Preço Rastreador GPRS/GSM (PF)", value=float(pf_prices.get("GPRS / Gsm", 0.0)), format="%.2f", key="pf_gprs")
                    pf_prices["Satelital"] = col2.number_input("Preço Rastreador Satelital (PF)", value=float(pf_prices.get("Satelital", 0.0)), format="%.2f", key="pf_satelital")

                with st.expander("Simulador Licitação (Custos)", expanded=True):
                    licit_prices = pricing_config.get("PRECO_CUSTO_LICITACAO", {})
                    l_col1, l_col2, l_col3 = st.columns(3)
                    licit_prices["Rastreador GPRS/GSM 2G"] = l_col1.number_input("Custo GPRS/GSM 2G", value=float(licit_prices.get("Rastreador GPRS/GSM 2G", 0.0)), format="%.2f")
                    licit_prices["Rastreador GPRS/GSM 4G"] = l_col2.number_input("Custo GPRS/GSM 4G", value=float(licit_prices.get("Rastreador GPRS/GSM 4G", 0.0)), format="%.2f")
                    licit_prices["Rastreador Satelital"] = l_col3.number_input("Custo Satelital", value=float(licit_prices.get("Rastreador Satelital", 0.0)), format="%.2f")
                    licit_prices["Telemetria/CAN"] = l_col1.number_input("Custo Telemetria/CAN", value=float(licit_prices.get("Telemetria/CAN", 0.0)), format="%.2f")
                    licit_prices["RFID - ID Motorista"] = l_col2.number_input("Custo RFID", value=float(licit_prices.get("RFID - ID Motorista", 0.0)), format="%.2f")

                with st.expander("Simulador Pessoa Jurídica (PJ)", expanded=True):
                    pj_plans = pricing_config.get("PLANOS_PJ", {})
                    for plan_name, products in pj_plans.items():
                        st.markdown(f"###### Plano: {plan_name}")
                        cols = st.columns(3)
                        product_keys = list(products.keys())
                        for i, key in enumerate(product_keys):
                            products[key] = cols[i % 3].number_input(f"Preço {key}", value=float(products.get(key, 0.0)), format="%.2f", key=f"pj_{plan_name}_{key}")

                if st.form_submit_button("✅ Salvar Todas as Alterações de Preços"):
                    new_config_data = pricing_config.copy()
                    new_config_data["PRECOS_PF"] = pf_prices
                    new_config_data["PRECO_CUSTO_LICITACAO"] = licit_prices
                    new_config_data["PLANOS_PJ"] = pj_plans
                    
                    if umdb.update_pricing_config(new_config_data):
                        umdb.add_log(username, "Atualizou Preços", "Todos os preços da plataforma foram alterados.")
                        st.toast("Preços atualizados com sucesso!", icon="🎉")
                    else:
                        st.error("Falha ao atualizar os preços.")

elif st.session_state["authentication_status"] is False:
    st.error('❌ Nome de utilizador ou senha incorreto(s).')
elif st.session_state["authentication_status"] is None:
    st.title("Simulador de Telemetria")
    st.info('👋 Por favor, insira o seu nome de utilizador e senha para aceder.')
