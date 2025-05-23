# Simulador_Comercial.py
import streamlit as st
import pandas as pd

# --- Configuração Inicial da Página ---
# Deve ser o primeiro comando Streamlit, exceto imports.
st.set_page_config(page_title="Simulador Telemetria Principal", layout="wide")

# --- Importação Segura do Módulo de Banco de Dados ---
try:
    import user_management_db as umdb
    print("INFO_LOG (Simulador_Comercial.py): Módulo user_management_db importado.")
except ModuleNotFoundError:
    st.error("ERRO CRÍTICO: O arquivo 'user_management_db.py' não foi encontrado.")
    st.info("Verifique se 'user_management_db.py' está na mesma pasta que 'Simulador_Comercial.py'.")
    print("CRITICAL_ERROR_LOG: user_management_db.py not found.")
    st.stop() 

# Tenta importar streamlit_authenticator APÓS verificar user_management_db
try:
    import streamlit_authenticator as stauth
    print("INFO_LOG (Simulador_Comercial.py): Módulo streamlit_authenticator importado.")
except ModuleNotFoundError:
    st.error("ERRO CRÍTICO: A biblioteca 'streamlit-authenticator' não está instalada.")
    st.info("Por favor, adicione 'streamlit-authenticator' ao seu arquivo requirements.txt e reinstale as dependências.")
    print("CRITICAL_ERROR_LOG: streamlit-authenticator not found.")
    st.stop()


# --- Carregamento de Credenciais e Verificação da Conexão com DB ---
print("INFO_LOG (Simulador_Comercial.py): Iniciando busca de credenciais...")
credentials = umdb.fetch_all_users_for_auth() # Espera {"usernames": {...}}
client_available = umdb.get_mongo_client() is not None 

# --- DEBUGGING (Descomente no Streamlit Cloud via Fork se precisar, ou adicione prints) ---
# print(f"DEBUG_LOG: client_available = {client_available}")
# print(f"DEBUG_LOG: credentials = {credentials}")
# No Streamlit Cloud, você pode ver esses prints nos logs do app.

# --- Configuração do Autenticador ---
auth_cookie_name = st.secrets.get("AUTH_COOKIE_NAME")
auth_cookie_key = st.secrets.get("AUTH_COOKIE_KEY")
auth_cookie_expiry_days = st.secrets.get("AUTH_COOKIE_EXPIRY_DAYS", 30) # Default de 30 dias

if not auth_cookie_name or not auth_cookie_key:
    st.error("ERRO DE CONFIGURAÇÃO: AUTH_COOKIE_NAME ou AUTH_COOKIE_KEY não definidos nos segredos do Streamlit Cloud.")
    print("CRITICAL_ERROR_LOG: Cookie secrets not configured in Streamlit Cloud.")
    st.info("Estes são necessários para o funcionamento seguro do login. Adicione-os nas configurações de segredos do seu app.")
    st.stop()

try:
    authenticator = stauth.Authenticate(
        credentials, # Passa o dicionário completo retornado por fetch_all_users_for_auth
        auth_cookie_name,
        auth_cookie_key,
        cookie_expiry_days=auth_cookie_expiry_days
    )
    print("INFO_LOG (Simulador_Comercial.py): Autenticador inicializado.")
except Exception as e:
    st.error(f"ERRO AO INICIALIZAR O AUTENTICADOR: {e}")
    print(f"AUTHENTICATOR_INIT_ERROR_LOG: {e}, Credentials type: {type(credentials)}")
    if isinstance(credentials, dict) and "usernames" not in credentials:
        print("AUTHENTICATOR_INIT_ERROR_LOG: 'usernames' key missing in credentials.")
    elif not isinstance(credentials, dict):
        print(f"AUTHENTICATOR_INIT_ERROR_LOG: 'credentials' is not a dict, it is {type(credentials)}.")
    st.stop()

# --- Lógica Principal da Aplicação ---

if not client_available:
    st.title("Simulador Telemetria")
    st.error("FALHA CRÍTICA NA CONEXÃO COM O BANCO DE DADOS.")
    st.info("O sistema de login e as funcionalidades dependentes estão indisponíveis. "
            "Verifique os logs do aplicativo no Streamlit Cloud para mensagens de erro do 'user_management_db.py'.")
    st.stop()

if not credentials.get("usernames"): # Se usernames está vazio e DB está disponível
    st.title("Bem-vindo ao Simulador Telemetria! 🚀")
    st.subheader("Configuração Inicial: Criar Conta de Administrador")
    print("INFO_LOG (Simulador_Comercial.py): Exibindo formulário de criação do primeiro admin.")
    with st.form("FormCriarPrimeiroAdmin"):
        admin_name = st.text_input("Nome Completo", key="init_admin_name_f")
        admin_username = st.text_input("Nome de Usuário (login)", key="init_admin_uname_f")
        admin_email = st.text_input("Email", key="init_admin_email_f")
        admin_password = st.text_input("Senha", type="password", key="init_admin_pass_f")
        submit_admin = st.form_submit_button("Criar Administrador")

        if submit_admin:
            if all([admin_name, admin_username, admin_email, admin_password]):
                if umdb.add_user(admin_username, admin_name, admin_email, admin_password, "admin"):
                    st.success("Conta de administrador criada! Recarregando para login...")
                    print(f"INFO_LOG (Simulador_Comercial.py): Primeiro admin '{admin_username}' criado.")
                    st.rerun() # Força o recarregamento para o authenticator pegar o novo usuário
            else:
                st.warning("Por favor, preencha todos os campos.")
    st.stop() 

# --- Processo de Login ---
print("INFO_LOG (Simulador_Comercial.py): Chamando authenticator.login()...")
try:
    name, authentication_status, username = authenticator.login(location='main')
except Exception as e:
    st.error(f"ERRO DURANTE authenticator.login(): {e}")
    print(f"AUTHENTICATOR_LOGIN_ERROR_LOG: {e}")
    st.info("Se o problema persistir, verifique os logs e a configuração do autenticador.")
    st.stop()

print(f"INFO_LOG (Simulador_Comercial.py): Login status: {authentication_status}, User: {username}")

if authentication_status is False:
    st.error("Nome de usuário ou senha incorreto(s). Tente novamente.")
elif authentication_status is None:
    st.info("Por favor, insira seu nome de usuário e senha para acessar o simulador.")
elif authentication_status: # True, login bem-sucedido
    st.session_state.name = name
    st.session_state.username = username
    st.session_state.authentication_status = authentication_status
    
    st.session_state.role = umdb.get_user_role(username)
    if st.session_state.role is None:
        st.error("ERRO: Não foi possível determinar seu nível de acesso. Tente fazer logout e login novamente.")
        print(f"ERROR_LOG (Simulador_Comercial.py): Falha ao obter role para usuário '{username}'.")
        authenticator.logout("Logout (Erro de Role)", "sidebar")
        st.stop()
    print(f"INFO_LOG (Simulador_Comercial.py): Usuário '{username}' logado com role '{st.session_state.role}'.")

    st.sidebar.title(f"Bem-vindo(a), {name}!")
    authenticator.logout("Logout", "sidebar")

    if st.session_state.role == "user":
        st.sidebar.subheader("Minha Conta")
        try:
            if authenticator.change_password(username, 'Alterar Senha', location='sidebar'):
                new_hashed_pass = authenticator.credentials['usernames'][username]['password']
                if umdb.update_user_password_self(username, new_hashed_pass):
                    st.sidebar.success('Senha alterada com sucesso!')
                else:
                    st.sidebar.error('Falha ao salvar nova senha no banco.')
        except Exception as e:
            st.sidebar.error(f"Erro ao tentar alterar senha: {e}")
            print(f"CHANGE_PASSWORD_ERROR_LOG: User '{username}', {e}")
        st.sidebar.info("Acesso de visualização aos simuladores.")

    elif st.session_state.role == "admin":
        st.sidebar.subheader("Painel de Administração")
        admin_action_options = ["Ver Usuários", "Cadastrar Novo Usuário", "Editar Usuário",
                                "Excluir Usuário", "Redefinir Senha de Usuário"]
        admin_action = st.sidebar.selectbox("Gerenciar Usuários", admin_action_options, key="admin_action_sb")
        
        current_db_users_info = umdb.fetch_all_users_for_auth().get("usernames", {})
        
        if admin_action == "Ver Usuários":
            st.subheader("Usuários Cadastrados")
            users_for_display = umdb.get_all_users_for_admin_display()
            if users_for_display:
                df_users = pd.DataFrame(users_for_display)
                st.dataframe(df_users, use_container_width=True, hide_index=True)
            else:
                st.info("Nenhum usuário cadastrado (ou falha ao buscar).")

        elif admin_action == "Cadastrar Novo Usuário":
            st.subheader("Cadastrar Novo Usuário")
            with st.form("form_admin_cadastrar_usuario", clear_on_submit=True):
                # ... (inputs como antes, com chaves únicas) ...
                reg_name_adm = st.text_input("Nome Completo", key="adm_reg_name_v2")
                reg_uname_adm = st.text_input("Nome de Usuário (login)", key="adm_reg_uname_v2")
                reg_email_adm = st.text_input("Email", key="adm_reg_email_v2")
                reg_pass_adm = st.text_input("Senha", type="password", key="adm_reg_pass_v2")
                reg_role_adm = st.selectbox("Papel", ["user", "admin"], key="adm_reg_role_v2")
                if st.form_submit_button("Cadastrar Usuário"):
                    if all([reg_name_adm, reg_uname_adm, reg_email_adm, reg_pass_adm, reg_role_adm]):
                        if umdb.add_user(reg_uname_adm, reg_name_adm, reg_email_adm, reg_pass_adm, reg_role_adm):
                            st.rerun() 
                    else:
                        st.warning("Preencha todos os campos.")
        
        elif admin_action == "Editar Usuário":
            st.subheader("Editar Usuário")
            if not current_db_users_info:
                st.info("Nenhum usuário para editar.")
            else:
                # ... (lógica de edição como antes, com chaves únicas) ...
                user_to_edit_uname = st.selectbox("Usuário a editar", list(current_db_users_info.keys()), key="adm_edit_sel_user_v2")
                if user_to_edit_uname:
                    user_data = current_db_users_info[user_to_edit_uname]
                    with st.form(f"form_edit_user_{user_to_edit_uname}", key=f"adm_edit_form_{user_to_edit_uname}_v2"):
                        edit_name = st.text_input("Nome", value=user_data.get('name', ''), key=f"adm_edit_name_{user_to_edit_uname}_v2")
                        edit_email = st.text_input("Email", value=user_data.get('email', ''), key=f"adm_edit_email_{user_to_edit_uname}_v2")
                        roles = ["user", "admin"]
                        current_role_idx = roles.index(user_data.get('role', 'user')) if user_data.get('role', 'user') in roles else 0
                        edit_role = st.selectbox("Papel", roles, index=current_role_idx, key=f"adm_edit_role_{user_to_edit_uname}_v2")
                        if st.form_submit_button("Salvar Alterações"):
                            if umdb.update_user_details(user_to_edit_uname, edit_name, edit_email, edit_role):
                                st.rerun()
        
        elif admin_action == "Excluir Usuário":
            st.subheader("Excluir Usuário")
            if not current_db_users_info:
                st.info("Nenhum usuário para excluir.")
            else:
                # ... (lógica de exclusão como antes, com chaves únicas) ...
                user_to_delete_uname = st.selectbox("Usuário a excluir", list(current_db_users_info.keys()), key="adm_del_sel_user_v2")
                if user_to_delete_uname:
                    st.warning(f"Confirma a exclusão de '{user_to_delete_uname}'?")
                    if st.button(f"Excluir {user_to_delete_uname}", type="primary", key=f"adm_del_btn_{user_to_delete_uname}_v2"):
                        if umdb.delete_user(user_to_delete_uname):
                            st.rerun()

        elif admin_action == "Redefinir Senha de Usuário":
            st.subheader("Redefinir Senha de Usuário")
            if not current_db_users_info:
                st.info("Nenhum usuário para redefinir senha.")
            else:
                # ... (lógica de redefinição de senha como antes, com chaves únicas) ...
                user_to_reset_uname = st.selectbox("Usuário", list(current_db_users_info.keys()), key="adm_reset_sel_user_v2")
                if user_to_reset_uname:
                    with st.form(f"form_reset_pass_{user_to_reset_uname}", clear_on_submit=True, key=f"adm_reset_form_{user_to_reset_uname}_v2"):
                        new_pass = st.text_input("Nova Senha", type="password", key=f"adm_reset_new_pass_{user_to_reset_uname}_v2")
                        confirm_pass = st.text_input("Confirmar Nova Senha", type="password", key=f"adm_reset_conf_pass_{user_to_reset_uname}_v2")
                        if st.form_submit_button("Redefinir Senha"):
                            if not new_pass: st.warning("Senha não pode ser vazia.")
                            elif new_pass != confirm_pass: st.warning("Senhas não coincidem.")
                            else:
                                if umdb.update_user_password_by_admin(user_to_reset_uname, new_pass):
                                    st.rerun()
        st.sidebar.info("Acesso de administrador.")

    st.markdown("---") 
    st.header("Simulador de Telemetria Principal")
    st.write("Navegue pelas funcionalidades usando o menu lateral.")
    # Adicione aqui o conteúdo da página principal após o login, se houver.
    # As páginas individuais estão na pasta 'pages/'.