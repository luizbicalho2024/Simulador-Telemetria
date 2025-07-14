# Simulador_Comercial.py (Versão Final Otimizada)
import streamlit as st
import pandas as pd

# --- Configuração da Página ---
st.set_page_config(page_title="Simulador Telemetria", layout="wide")

# --- Importação Segura e Inicialização de Módulos ---
# Usando a estrutura exata do seu user_management_db.py
try:
    import user_management_db as umdb
    import streamlit_authenticator as stauth
    from streamlit_authenticator.utilities.hasher import Hasher
    print("INFO_LOG: Módulos de autenticação e DB importados.")
except (ModuleNotFoundError, ImportError) as e:
    st.error(f"ERRO CRÍTICO: Biblioteca essencial não encontrada ({e}). Verifique o 'requirements.txt'.")
    st.stop()

# --- Verificação da Conexão com o Banco de Dados ---
# A função get_mongo_client já mostra erros na tela se falhar.
if not umdb.get_mongo_client():
    st.title("Simulador Telemetria")
    st.error("FALHA CRÍTICA NA CONEXÃO COM O BANCO DE DADOS. Verifique os 'Secrets' no Streamlit Cloud.")
    st.stop()

# --- Carregamento de Credenciais e Configuração do Autenticador ---
credentials = umdb.fetch_all_users_for_auth()
auth_cookie_name = st.secrets.get("AUTH_COOKIE_NAME", "default_cookie_name")
auth_cookie_key = st.secrets.get("AUTH_COOKIE_KEY", "default_secret_key")
auth_cookie_expiry = st.secrets.get("AUTH_COOKIE_EXPIRY_DAYS", 30)

authenticator = stauth.Authenticate(
    credentials,
    auth_cookie_name,
    auth_cookie_key,
    cookie_expiry_days=auth_cookie_expiry
)

# --- Lógica Principal da Aplicação ---

# 1. Criação do Primeiro Administrador (se o DB estiver vazio)
if not credentials.get("usernames"):
    st.title("Bem-vindo ao Simulador Telemetria! 🚀")
    st.subheader("Configuração Inicial: Criar Conta de Administrador")
    with st.form("FormCriarPrimeiroAdmin"):
        admin_name = st.text_input("Nome Completo")
        admin_username = st.text_input("Nome de Usuário (login)")
        admin_email = st.text_input("Email")
        admin_password = st.text_input("Senha", type="password")
        if st.form_submit_button("Criar Administrador"):
            if all([admin_name, admin_username, admin_email, admin_password]):
                # A função add_user agora lida com o hashing internamente
                if umdb.add_user(admin_username, admin_name, admin_email, admin_password, "admin"):
                    st.success("Conta de administrador criada! A página será recarregada.")
                    st.rerun()
            else:
                st.warning("Preencha todos os campos.")
    st.stop()

# 2. Processo de Login
name, authentication_status, username = authenticator.login(location='main')

if authentication_status is False:
    st.error("Nome de usuário ou senha incorreto(s).")
elif authentication_status is None:
    st.info("Por favor, insira seu nome de usuário e senha.")
elif authentication_status:
    # --- Login bem-sucedido ---
    st.session_state.name = name
    st.session_state.username = username
    st.session_state.authentication_status = authentication_status
    st.session_state.role = umdb.get_user_role(username)

    if st.session_state.role is None:
        st.error("ERRO PÓS-LOGIN: Não foi possível determinar seu nível de acesso.")
        authenticator.logout("Logout", "sidebar")
        st.stop()

    st.sidebar.title(f"Bem-vindo(a), {name}!")
    authenticator.logout("Sair", "sidebar")

    # --- Lógica de Interface Pós-Login ---
    # Painel do Usuário Comum
    if st.session_state.role == "user":
        st.sidebar.subheader("Minha Conta")
        with st.sidebar.expander("Alterar Minha Senha"):
            with st.form("form_user_change_password", clear_on_submit=True):
                current_password = st.text_input("Senha Atual", type="password")
                new_password = st.text_input("Nova Senha", type="password")
                if st.form_submit_button("Salvar Nova Senha"):
                    stored_hash = umdb.get_user_hashed_password(username)
                    if stored_hash and Hasher([current_password]).verify(stored_hash):
                        if umdb.update_user_password_manual(username, new_password):
                            st.success("Senha alterada com sucesso!")
                        else:
                            st.error("Falha ao atualizar a senha.")
                    else:
                        st.error("Senha atual incorreta.")

    # Painel de Administração (com st.tabs para melhor UX)
    elif st.session_state.role == "admin":
        st.sidebar.subheader("Painel de Admin")
        tab_ver, tab_cad, tab_edit, tab_reset, tab_del = st.tabs(["Ver", "Cadastrar", "Editar", "Resetar Senha", "Excluir"])

        with tab_ver:
            st.dataframe(umdb.get_all_users_for_admin_display(), use_container_width=True, hide_index=True)

        with tab_cad:
            with st.form("form_cadastrar", clear_on_submit=True):
                uname = st.text_input("Username")
                nome = st.text_input("Nome Completo")
                mail = st.text_input("Email")
                pwd = st.text_input("Senha", type="password")
                role = st.selectbox("Papel", ["user", "admin"])
                if st.form_submit_button("Cadastrar"):
                    umdb.add_user(uname, nome, mail, pwd, role)
                    st.rerun()

        users_dict = {u['username']: u for u in umdb.get_all_users_for_admin_display()}
        if users_dict:
            user_to_manage = st.selectbox("Selecione um usuário para gerenciar:", list(users_dict.keys()))

            with tab_edit:
                user_data = users_dict.get(user_to_manage)
                if user_data:
                    with st.form(f"form_edit_{user_to_manage}"):
                        new_name = st.text_input("Nome", value=user_data.get('name', ''))
                        new_email = st.text_input("Email", value=user_data.get('email', ''))
                        new_role = st.selectbox("Papel", ["user", "admin"], index=["user", "admin"].index(user_data.get('role', 'user')))
                        if st.form_submit_button("Salvar Alterações"):
                            umdb.update_user_details(user_to_manage, new_name, new_email, new_role)
                            st.rerun()
            with tab_reset:
                with st.form(f"form_reset_{user_to_manage}", clear_on_submit=True):
                    new_pwd = st.text_input("Nova Senha", type="password")
                    if st.form_submit_button("Resetar Senha"):
                        umdb.update_user_password_by_admin(user_to_manage, new_pwd)
                        st.rerun()
            with tab_del:
                if st.button(f"Excluir '{user_to_manage}'", type="primary"):
                    if umdb.delete_user(user_to_manage):
                        st.rerun()
        else:
            st.info("Nenhum usuário cadastrado para gerenciar.")


    # --- Conteúdo Principal da Página ---
    st.markdown("---")
    st.header("Simulador de Telemetria Principal")
    st.write("Navegue pelas funcionalidades usando o menu lateral.")
