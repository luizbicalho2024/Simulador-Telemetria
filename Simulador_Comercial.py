# Simulador_Comercial.py
import streamlit as st
import pandas as pd

# --- Configuração Inicial da Página ---
st.set_page_config(page_title="Simulador Telemetria", layout="wide")

# --- Importação Segura e Inicialização de Módulos ---
try:
    import user_management_db as umdb
    from streamlit_authenticator.utilities.hasher import Hasher
    import streamlit_authenticator as stauth
except (ModuleNotFoundError, ImportError) as e:
    st.error(f"ERRO CRÍTICO: Uma biblioteca essencial não foi encontrada ({e}). Verifique o 'requirements.txt' e a instalação.")
    st.stop()

# --- Carregamento de Credenciais e Configuração do Autenticador ---
credentials = umdb.fetch_all_users_for_auth()
auth_cookie_name = st.secrets.get("AUTH_COOKIE_NAME", "some_cookie_name")
auth_cookie_key = st.secrets.get("AUTH_COOKIE_KEY", "some_signature_key")
auth_cookie_expiry_days = st.secrets.get("AUTH_COOKIE_EXPIRY_DAYS", 30)

authenticator = stauth.Authenticate(
    credentials,
    auth_cookie_name,
    auth_cookie_key,
    cookie_expiry_days=auth_cookie_expiry_days
)

# --- Lógica Principal ---

# 1. Checagem de Conexão com o Banco de Dados
if not umdb.get_mongo_client():
    st.title("Simulador Telemetria")
    st.error("FALHA CRÍTICA NA CONEXÃO COM O BANCO DE DADOS.")
    st.stop()

# 2. Formulário de Criação do Primeiro Administrador (se não houver usuários)
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
                if umdb.add_user(admin_username, admin_name, admin_email, admin_password, "admin"):
                    st.success("Conta de administrador criada! Recarregando...")
                    st.rerun()
            else:
                st.warning("Preencha todos os campos.")
    st.stop()

# 3. Processo de Login
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

    # --- SEÇÕES DE USUÁRIO E ADMIN ---
    if st.session_state.role == "user":
        st.sidebar.subheader("Minha Conta")
        with st.sidebar.expander("Alterar Minha Senha"):
            with st.form("form_user_change_password", clear_on_submit=True):
                current_password = st.text_input("Senha Atual", type="password")
                new_password = st.text_input("Nova Senha", type="password")
                confirm_new_password = st.text_input("Confirmar Nova Senha", type="password")
                if st.form_submit_button("Salvar Nova Senha"):
                    if not all([current_password, new_password, confirm_new_password]):
                        st.warning("Todos os campos de senha são obrigatórios.")
                    elif new_password != confirm_new_password:
                        st.error("A nova senha e a confirmação não coincidem.")
                    else:
                        stored_hashed_password = umdb.get_user_hashed_password(username)
                        if stored_hashed_password and umdb.verify_password(current_password, stored_hashed_password):
                            if umdb.update_user_password_manual(username, new_password):
                                st.success("Senha alterada! Faça logout e login novamente para aplicar.")
                            else:
                                st.error("Falha ao atualizar a senha no banco de dados.")
                        else:
                            st.error("Senha atual incorreta.")
        st.sidebar.info("Acesso de visualização aos simuladores.")

    elif st.session_state.role == "admin":
        st.sidebar.subheader("Painel de Administração")
        st.sidebar.info("Acesso de administrador.")
        
        tab_ver, tab_cadastrar, tab_editar, tab_redefinir, tab_excluir = st.tabs([
            "👁️ Ver Usuários", "➕ Cadastrar", "✏️ Editar", "🔑 Redefinir Senha", "🗑️ Excluir"
        ])

        with tab_ver:
            st.subheader("Usuários Cadastrados")
            users_for_display = umdb.get_all_users_for_admin_display()
            if users_for_display:
                st.dataframe(pd.DataFrame(users_for_display), use_container_width=True, hide_index=True)
            else:
                st.info("Nenhum usuário cadastrado.")

        with tab_cadastrar:
            st.subheader("Cadastrar Novo Usuário")
            with st.form("form_admin_cadastrar_usuario", clear_on_submit=True):
                reg_name = st.text_input("Nome Completo")
                reg_uname = st.text_input("Nome de Usuário (login)")
                reg_email = st.text_input("Email")
                reg_pass = st.text_input("Senha", type="password")
                reg_role = st.selectbox("Papel", ["user", "admin"])
                if st.form_submit_button("Cadastrar Usuário"):
                    if all([reg_name, reg_uname, reg_email, reg_pass, reg_role]):
                        if umdb.add_user(reg_uname, reg_name, reg_email, reg_pass, reg_role):
                            st.rerun()
                    else:
                        st.warning("Preencha todos os campos.")

        with tab_editar:
            st.subheader("⚙️ Editar Usuário")
            users_dict = {user['username']: user for user in umdb.get_all_users_for_admin_display()}
            if not users_dict:
                st.info("Nenhum usuário disponível para edição.")
            else:
                user_to_edit = st.selectbox("Usuário a editar:", list(users_dict.keys()))
                user_data = users_dict.get(user_to_edit)
                if user_data:
                    with st.form(f"form_edit_user_{user_to_edit}", clear_on_submit=False):
                        edit_name = st.text_input("Nome Completo:", value=user_data.get('name', ''))
                        edit_email = st.text_input("Email:", value=user_data.get('email', ''))
                        roles_options = ["user", "admin"]
                        current_role_idx = roles_options.index(user_data.get('role', 'user'))
                        edit_role = st.selectbox("Novo Papel:", roles_options, index=current_role_idx)
                        if st.form_submit_button("Salvar Alterações"):
                            if umdb.update_user_details(user_to_edit, edit_name, edit_email, edit_role):
                                st.rerun()

        with tab_redefinir:
            st.subheader("🔑 Redefinir Senha de Usuário")
            users_list = [user['username'] for user in umdb.get_all_users_for_admin_display()]
            if not users_list:
                st.info("Nenhum usuário disponível.")
            else:
                user_to_reset = st.selectbox("Usuário para redefinir senha:", users_list)
                with st.form(f"form_reset_pass_{user_to_reset}", clear_on_submit=True):
                    new_pass = st.text_input("Nova Senha:", type="password")
                    confirm_pass = st.text_input("Confirmar Nova Senha:", type="password")
                    if st.form_submit_button("Redefinir Senha"):
                        if not new_pass:
                            st.warning("A nova senha não pode ser vazia.")
                        elif new_pass != confirm_pass:
                            st.warning("As senhas não coincidem.")
                        else:
                            umdb.update_user_password_by_admin(user_to_reset, new_pass)

        with tab_excluir:
            st.subheader("🗑️ Excluir Usuário")
            users_list_delete = [user['username'] for user in umdb.get_all_users_for_admin_display()]
            if not users_list_delete:
                st.info("Nenhum usuário para excluir.")
            else:
                user_to_delete = st.selectbox("Usuário a excluir:", users_list_delete)
                if st.button(f"Excluir Permanentemente '{user_to_delete}'", type="primary"):
                    if umdb.delete_user(user_to_delete):
                        st.rerun()
                        
    # --- Conteúdo Principal da Página Pós-Login ---
    st.markdown("---")
    st.header("Simulador de Telemetria Principal")
    st.write("Navegue pelas funcionalidades usando o menu lateral.")
    st.info("Use `st.page_link` para navegar entre as páginas de forma programática.")
    if st.button("Ir para o Simulador PJ"):
        st.switch_page("pages/Simulador_PJ.py")
