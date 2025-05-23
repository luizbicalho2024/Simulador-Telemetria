# Simulador_Comercial.py
import streamlit as st
import streamlit_authenticator as stauth
import pandas as pd

try:
    import user_management_db as umdb
except ModuleNotFoundError:
    st.error("ERRO CRÍTICO: O arquivo 'user_management_db.py' não foi encontrado.")
    st.info("Certifique-se de que 'user_management_db.py' está na mesma pasta que 'Simulador_Comercial.py'.")
    st.stop()

st.set_page_config(page_title="Simulador Telemetria", layout="wide")

credentials = umdb.fetch_all_users_for_auth()

# --- DEBUGGING BLOCK ---
st.sidebar.subheader("Debug: 'credentials'")
if isinstance(credentials, dict):
    st.sidebar.json(credentials)
    if not credentials.get("usernames"):
        st.sidebar.warning("Debug: 'credentials[usernames]' está vazio ou não existe.")
else:
    st.sidebar.error(f"Debug: 'credentials' não é um dicionário. Tipo: {type(credentials)}")
st.sidebar.markdown("---")
# --- END DEBUGGING BLOCK ---

auth_cookie_name = st.secrets.get("AUTH_COOKIE_NAME", "simulador_auth_cookie_fallback")
auth_cookie_key = st.secrets.get("AUTH_COOKIE_KEY", "fallback_secret_key_please_change")
auth_cookie_expiry_days = st.secrets.get("AUTH_COOKIE_EXPIRY_DAYS", 30)

if auth_cookie_name == "simulador_auth_cookie_fallback" or auth_cookie_key == "fallback_secret_key_please_change":
    st.warning("ALERTA: Chaves de autenticação (AUTH_COOKIE_NAME/AUTH_COOKIE_KEY) não encontradas em secrets.toml. Usando fallbacks inseguros.")

# CORREÇÃO: Removido o argumento 'preauthorized'
authenticator = stauth.Authenticate(
    credentials.get("usernames", {}),
    auth_cookie_name,
    auth_cookie_key,
    cookie_expiry_days=auth_cookie_expiry_days
)

client_available = umdb.get_mongo_client() is not None

if not credentials.get("usernames") and client_available:
    st.title("Bem-vindo ao Simulador! 🚀")
    st.subheader("Configuração Inicial: Criar Conta de Administrador")
    with st.form("Criar Primeiro Admin"):
        admin_name = st.text_input("Nome Completo", key="init_admin_name")
        admin_username = st.text_input("Nome de Usuário (para login)", key="init_admin_uname")
        admin_email = st.text_input("Email", key="init_admin_email")
        admin_password = st.text_input("Senha", type="password", key="init_admin_pass")
        submit_admin = st.form_submit_button("Criar Administrador")

        if submit_admin:
            if admin_name and admin_username and admin_email and admin_password:
                if umdb.add_user(admin_username, admin_name, admin_email, admin_password, "admin"):
                    st.success("Conta de administrador criada! Por favor, atualize a página (F5) ou clique abaixo para fazer login.")
                    if st.button("Recarregar para Login"):
                        st.rerun()
            else:
                st.warning("Por favor, preencha todos os campos.")
    st.stop()
elif not client_available:
    st.title("Simulador Telemetria")
    st.error("FALHA CRÍTICA: Não foi possível conectar ao banco de dados.")
    st.info("As funcionalidades de login e gerenciamento de usuários estão indisponíveis. Verifique as mensagens de erro no console ou nos logs, e confira a configuração do arquivo '.streamlit/secrets.toml' e o acesso à rede do MongoDB Atlas.")
    st.stop()

name, authentication_status, username = authenticator.login(location='main')

if authentication_status is False:
    st.error("Nome de usuário ou senha incorreto(s).")
elif authentication_status is None:
    st.info("Por favor, insira seu nome de usuário e senha para acessar o simulador.")
elif authentication_status:
    if "role" not in st.session_state or st.session_state.get("username") != username:
        st.session_state.username = username
        st.session_state.name = name
        st.session_state.role = umdb.get_user_role(username)
        if st.session_state.role is None:
            st.error("Não foi possível determinar o seu nível de acesso. Por favor, faça logout e tente novamente.")
            authenticator.logout("Logout Problemático", "sidebar")
            st.stop()

    st.sidebar.title(f"Bem-vindo(a), {st.session_state.get('name', username)}!")
    authenticator.logout("Logout", "sidebar")

    if st.session_state.role == "user":
        st.sidebar.subheader("Minha Conta")
        try:
            if authenticator.change_password(username, 'Alterar Senha', location='sidebar'):
                new_hashed_password = authenticator.credentials['usernames'][username]['password']
                if umdb.update_user_password_self(username, new_hashed_password):
                    st.sidebar.success('Senha alterada com sucesso no banco de dados!')
                else:
                    st.sidebar.error('Falha ao salvar a nova senha no banco. Tente novamente ou contate o suporte.')
        except Exception as e:
            st.sidebar.error(f"Erro ao tentar alterar senha: {e}")
        st.sidebar.info("Você tem acesso de visualização aos simuladores.")

    elif st.session_state.role == "admin":
        st.sidebar.subheader("Painel de Administração")
        admin_action = st.sidebar.selectbox(
            "Gerenciar Usuários",
            ["Ver Usuários", "Cadastrar Novo Usuário", "Editar Usuário",
             "Excluir Usuário", "Redefinir Senha de Usuário"],
            key="admin_action_select"
        )

        if admin_action == "Ver Usuários":
            st.subheader("Usuários Cadastrados")
            all_users_data = umdb.get_all_users_for_admin_display()
            if all_users_data:
                df_users = pd.DataFrame(all_users_data)
                st.dataframe(df_users, use_container_width=True, hide_index=True)
            else:
                st.info("Nenhum usuário cadastrado.")

        elif admin_action == "Cadastrar Novo Usuário":
            st.subheader("Cadastrar Novo Usuário")
            with st.form("form_cadastrar_usuario", clear_on_submit=True):
                reg_name = st.text_input("Nome Completo", key="reg_name_admin")
                reg_username = st.text_input("Nome de Usuário (login)", key="reg_uname_admin")
                reg_email = st.text_input("Email", key="reg_email_admin")
                reg_password = st.text_input("Senha", type="password", key="reg_pass_admin")
                reg_role = st.selectbox("Papel (Role)", ["user", "admin"], key="reg_role_admin")
                submit_button = st.form_submit_button("Cadastrar Usuário")
                if submit_button:
                    if reg_name and reg_username and reg_email and reg_password and reg_role:
                        if umdb.add_user(reg_username, reg_name, reg_email, reg_password, reg_role):
                            st.success(f"Usuário {reg_username} adicionado. A lista será atualizada.")
                            st.rerun()
                    else:
                        st.warning("Por favor, preencha todos os campos.")

        elif admin_action == "Editar Usuário":
            st.subheader("Editar Usuário")
            users_for_auth = umdb.fetch_all_users_for_auth().get("usernames", {})
            if not users_for_auth:
                st.info("Nenhum usuário disponível para edição.")
            else:
                users_list_for_edit = list(users_for_auth.keys())
                selected_user_to_edit = st.selectbox("Selecione o usuário para editar", users_list_for_edit, key="edit_user_select_admin")
                if selected_user_to_edit:
                    user_data_to_edit = users_for_auth.get(selected_user_to_edit)
                    if user_data_to_edit:
                        with st.form(f"form_edit_user_{selected_user_to_edit}", key=f"edit_form_key_{selected_user_to_edit}"):
                            edit_name = st.text_input("Nome Completo", value=user_data_to_edit.get('name', ''), key=f"edit_name_val_{selected_user_to_edit}")
                            edit_email = st.text_input("Email", value=user_data_to_edit.get('email', ''), key=f"edit_email_val_{selected_user_to_edit}")
                            current_role = user_data_to_edit.get('role', 'user')
                            role_options = ["user", "admin"]
                            try:
                                current_role_index = role_options.index(current_role)
                            except ValueError:
                                current_role_index = 0
                            edit_role = st.selectbox("Papel (Role)", role_options, index=current_role_index, key=f"edit_role_val_{selected_user_to_edit}")
                            submit_edit = st.form_submit_button("Salvar Alterações")
                            if submit_edit:
                                if umdb.update_user_details(selected_user_to_edit, edit_name, edit_email, edit_role):
                                    st.success(f"Usuário {selected_user_to_edit} atualizado. A lista será atualizada.")
                                    st.rerun()
                    else:
                        st.error(f"Não foi possível carregar os dados do usuário '{selected_user_to_edit}' para edição.")

        elif admin_action == "Excluir Usuário":
            st.subheader("Excluir Usuário")
            users_for_auth_del = umdb.fetch_all_users_for_auth().get("usernames", {})
            if not users_for_auth_del:
                 st.info("Nenhum usuário para excluir.")
            else:
                users_list_for_delete = list(users_for_auth_del.keys())
                selected_user_to_delete = st.selectbox("Selecione o usuário para excluir", users_list_for_delete, key="delete_user_select_admin")
                if selected_user_to_delete:
                    st.warning(f"Tem certeza que deseja excluir o usuário '{selected_user_to_delete}'? Esta ação é irreversível.")
                    if st.button(f"Confirmar Exclusão de {selected_user_to_delete}", type="primary", key=f"del_btn_key_{selected_user_to_delete}"):
                        if umdb.delete_user(selected_user_to_delete):
                            st.success(f"Usuário {selected_user_to_delete} excluído. A lista será atualizada.")
                            st.rerun()
        
        elif admin_action == "Redefinir Senha de Usuário":
            st.subheader("Redefinir Senha de Usuário")
            users_for_auth_reset = umdb.fetch_all_users_for_auth().get("usernames", {})
            if not users_for_auth_reset:
                st.info("Nenhum usuário disponível para redefinir senha.")
            else:
                users_list_for_reset = list(users_for_auth_reset.keys())
                selected_user_to_reset_pass = st.selectbox("Selecione o usuário", users_list_for_reset, key="reset_pass_select_admin")
                if selected_user_to_reset_pass:
                    with st.form(f"form_reset_senha_{selected_user_to_reset_pass}", clear_on_submit=True, key=f"reset_form_key_{selected_user_to_reset_pass}"):
                        new_plain_password = st.text_input("Nova Senha", type="password", key=f"reset_pass_new_val_{selected_user_to_reset_pass}")
                        confirm_password = st.text_input("Confirmar Nova Senha", type="password", key=f"reset_pass_confirm_val_{selected_user_to_reset_pass}")
                        submit_reset = st.form_submit_button("Redefinir Senha")
                        if submit_reset:
                            if not new_plain_password:
                                st.warning("O campo Nova Senha não pode estar vazio.")
                            elif new_plain_password != confirm_password:
                                st.warning("As senhas não coincidem.")
                            else:
                                if umdb.update_user_password_by_admin(selected_user_to_reset_pass, new_plain_password):
                                    st.success(f"Senha para {selected_user_to_reset_pass} redefinida. A lista será atualizada.")
                                    st.rerun()
        st.sidebar.info("Você tem acesso total como administrador.")

    st.markdown("---")
    st.header("Simulador de Telemetria")
    st.write("Bem-vindo ao sistema! Use o menu na barra lateral para navegar entre as funcionalidades e opções da sua conta.")
    st.write("As páginas específicas do simulador estão disponíveis no menu de navegação que aparece ao expandir a seção de 'Páginas' (se houver páginas na pasta `pages`).")