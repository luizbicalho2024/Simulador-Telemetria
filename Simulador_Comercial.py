# Simulador_Comercial.py
import streamlit as st
import pandas as pd

# --- Configuração Inicial da Página ---
st.set_page_config(page_title="Simulador Telemetria Principal", layout="wide")
print("INFO_LOG (Simulador_Comercial.py): Página configurada.")

# --- Importação Segura do Módulo de Banco de Dados ---
try:
    import user_management_db as umdb
    print("INFO_LOG (Simulador_Comercial.py): Módulo user_management_db importado com sucesso.")
except ModuleNotFoundError:
    st.error("ERRO CRÍTICO: O arquivo 'user_management_db.py' não foi encontrado.")
    st.info("Verifique se 'user_management_db.py' está na mesma pasta que 'Simulador_Comercial.py'.")
    print("CRITICAL_ERROR_LOG (Simulador_Comercial.py): user_management_db.py não encontrado.")
    st.stop()

# --- Importação Segura do Streamlit Authenticator ---
try:
    import streamlit_authenticator as stauth
    print("INFO_LOG (Simulador_Comercial.py): Módulo streamlit_authenticator importado com sucesso.")
except ModuleNotFoundError:
    st.error("ERRO CRÍTICO: A biblioteca 'streamlit-authenticator' não está instalada.")
    st.info("Adicione 'streamlit-authenticator' ao seu arquivo requirements.txt e faça o deploy novamente.")
    print("CRITICAL_ERROR_LOG (Simulador_Comercial.py): streamlit-authenticator não encontrado.")
    st.stop()

# --- Carregamento de Credenciais e Verificação da Conexão com DB ---
print("INFO_LOG (Simulador_Comercial.py): Tentando buscar credenciais do banco de dados...")
credentials = umdb.fetch_all_users_for_auth() # Espera {"usernames": {...}}
client_available = umdb.get_mongo_client() is not None

# --- DEBUGGING (Verifique os logs no Streamlit Cloud) ---
print(f"DEBUG_LOG (Simulador_Comercial.py): client_available = {client_available}")
print(f"DEBUG_LOG (Simulador_Comercial.py): credentials = {credentials}")
if isinstance(credentials, dict) and not credentials.get("usernames"):
    print("DEBUG_LOG (Simulador_Comercial.py): 'credentials[\"usernames\"]' está vazio ou não existe.")


# --- Configuração do Autenticador ---
auth_cookie_name = st.secrets.get("AUTH_COOKIE_NAME")
auth_cookie_key = st.secrets.get("AUTH_COOKIE_KEY")
auth_cookie_expiry_days = st.secrets.get("AUTH_COOKIE_EXPIRY_DAYS", 30)

if not auth_cookie_name or not auth_cookie_key:
    st.error("ERRO DE CONFIGURAÇÃO CRÍTICO: AUTH_COOKIE_NAME ou AUTH_COOKIE_KEY não definidos nos segredos do Streamlit Cloud.")
    print("CRITICAL_ERROR_LOG (Simulador_Comercial.py): AUTH_COOKIE_NAME ou AUTH_COOKIE_KEY não encontrados nos segredos.")
    st.info("Estes são necessários para o login. Adicione-os nas configurações de 'Secrets' do seu app no Streamlit Cloud.")
    st.stop()

try:
    print("INFO_LOG (Simulador_Comercial.py): Tentando inicializar o Authenticator...")
    authenticator = stauth.Authenticate(
        credentials,
        auth_cookie_name,
        auth_cookie_key,
        cookie_expiry_days=auth_cookie_expiry_days
    )
    print("INFO_LOG (Simulador_Comercial.py): Autenticador inicializado com sucesso.")
except Exception as e:
    st.error(f"ERRO CRÍTICO AO INICIALIZAR O AUTENTICADOR: {e}")
    print(f"AUTHENTICATOR_INIT_ERROR_LOG (Simulador_Comercial.py): {e}, Credentials type: {type(credentials)}, Credentials content: {credentials}")
    if isinstance(credentials, dict) and "usernames" not in credentials:
        print("AUTHENTICATOR_INIT_ERROR_LOG (Simulador_Comercial.py): A chave 'usernames' está faltando no dicionário 'credentials'.")
    st.stop()

# --- Lógica Principal da Aplicação ---

if not client_available:
    st.title("Simulador Telemetria")
    st.error("FALHA CRÍTICA NA CONEXÃO COM O BANCO DE DADOS.")
    st.info("O sistema de login e as funcionalidades dependentes estão indisponíveis. "
            "Verifique os logs do aplicativo no Streamlit Cloud para mensagens de erro de 'user_management_db.py', "
            "especialmente sobre MONGO_CONNECTION_STRING e acesso à rede do MongoDB Atlas.")
    print("CRITICAL_ERROR_LOG (Simulador_Comercial.py): client_available é False. Conexão com DB falhou.")
    st.stop()

if not credentials.get("usernames"): # Se usernames está vazio e DB está (ou deveria estar) disponível
    st.title("Bem-vindo ao Simulador Telemetria! 🚀")
    st.subheader("Configuração Inicial: Criar Conta de Administrador")
    print("INFO_LOG (Simulador_Comercial.py): Exibindo formulário de criação do primeiro admin (credentials['usernames'] está vazio).")
    with st.form("FormCriarPrimeiroAdmin"):
        admin_name = st.text_input("Nome Completo", key="init_admin_name_v3")
        admin_username = st.text_input("Nome de Usuário (login)", key="init_admin_uname_v3")
        admin_email = st.text_input("Email", key="init_admin_email_v3")
        admin_password = st.text_input("Senha", type="password", key="init_admin_pass_v3")
        submit_admin = st.form_submit_button("Criar Administrador")

        if submit_admin:
            if all([admin_name, admin_username, admin_email, admin_password]):
                if umdb.add_user(admin_username, admin_name, admin_email, admin_password, "admin"):
                    st.success("Conta de administrador criada! Recarregando para login...")
                    print(f"INFO_LOG (Simulador_Comercial.py): Primeiro admin '{admin_username}' criado.")
                    st.rerun()
            else:
                st.warning("Por favor, preencha todos os campos.")
    st.stop()

# --- Processo de Login ---
print("INFO_LOG (Simulador_Comercial.py): Preparando para chamar authenticator.login()...")
print(f"DEBUG_LOG (Simulador_Comercial.py): Tipo do objeto authenticator: {type(authenticator)}")
print(f"DEBUG_LOG (Simulador_Comercial.py): Estado de st.session_state ANTES do login: {st.session_state.to_dict()}")


name, authentication_status, username = None, None, None # Inicializa para segurança
login_attempted = False

try:
    # A chamada original que estava causando o erro
    login_return_value = authenticator.login(location='main')
    login_attempted = True # Indica que a função login foi chamada

    print(f"DEBUG_LOG (Simulador_Comercial.py): Valor retornado por authenticator.login(): {login_return_value}")
    print(f"DEBUG_LOG (Simulador_Comercial.py): Tipo do valor retornado: {type(login_return_value)}")

    if login_return_value is not None and isinstance(login_return_value, tuple) and len(login_return_value) == 3:
        name, authentication_status, username = login_return_value
        print(f"INFO_LOG (Simulador_Comercial.py): authenticator.login() retornou: name='{name}', status={authentication_status}, username='{username}'")
    elif login_return_value is None:
        print("WARN_LOG (Simulador_Comercial.py): authenticator.login() retornou None. Isso é INESPERADO se o formulário foi submetido ou um cookie válido existe.")
        # Mantém name, authentication_status, username como None, o que acionará a lógica de "aguardando login".
        # Se o formulário de login não foi submetido, o comportamento esperado seria (None, None, None) ou dados do cookie.
        # Um retorno direto de 'None' pode indicar um problema mais sério no estado interno do authenticator.
        authentication_status = None # Garante que caia no bloco 'aguardando login'
    else:
        st.error("ERRO INESPERADO NO LOGIN: authenticator.login() retornou um valor malformado.")
        print(f"UNEXPECTED_LOGIN_RETURN_ERROR_LOG (Simulador_Comercial.py): Valor: {login_return_value}, Tipo: {type(login_return_value)}")
        st.stop()

except Exception as e:
    st.error(f"ERRO CRÍTICO DURANTE authenticator.login(): {e}")
    print(f"CRITICAL_AUTHENTICATOR_LOGIN_ERROR_LOG (Simulador_Comercial.py): Exception: {e}")
    print(f"DEBUG_LOG (Simulador_Comercial.py): Estado de st.session_state NO MOMENTO DA EXCEÇÃO em authenticator.login(): {st.session_state.to_dict()}")
    st.info("Ocorreu um erro inesperado durante o processo de login. Verifique os logs para mais detalhes.")
    st.stop()

print(f"INFO_LOG (Simulador_Comercial.py): Após authenticator.login() - Status: {authentication_status}, Usuário: {username}")

if authentication_status is False:
    st.error("Nome de usuário ou senha incorreto(s). Tente novamente.")
    print(f"INFO_LOG (Simulador_Comercial.py): Falha na autenticação para o usuário que tentou logar.")
elif authentication_status is None:
    # Isso acontece se o formulário de login ainda não foi enviado
    # ou se login_return_value foi None (indicando um possível problema)
    if login_attempted and login_return_value is None:
        st.warning("Ocorreu um problema ao processar o login. Por favor, tente novamente.")
    else:
        st.info("Por favor, insira seu nome de usuário e senha para acessar o simulador.")
    print(f"INFO_LOG (Simulador_Comercial.py): Aguardando submissão do formulário de login.")
elif authentication_status: # True, login bem-sucedido
    st.session_state.name = name
    st.session_state.username = username
    st.session_state.authentication_status = authentication_status
    
    st.session_state.role = umdb.get_user_role(username)
    if st.session_state.role is None:
        st.error("ERRO: Não foi possível determinar seu nível de acesso após o login. "
                 "Tente fazer logout e login novamente ou contate o suporte.")
        print(f"ERROR_LOG (Simulador_Comercial.py): Falha ao obter role para usuário '{username}'.")
        authenticator.logout("Logout (Erro de Role)", "sidebar")
        st.stop()
    print(f"INFO_LOG (Simulador_Comercial.py): Usuário '{username}' logado com sucesso. Role: '{st.session_state.role}'.")

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
            print(f"CHANGE_PASSWORD_ERROR_LOG (Simulador_Comercial.py): User '{username}', {e}")
        st.sidebar.info("Acesso de visualização aos simuladores.")

    elif st.session_state.role == "admin":
        st.sidebar.subheader("Painel de Administração")
        admin_action_options = ["Ver Usuários", "Cadastrar Novo Usuário", "Editar Usuário",
                                "Excluir Usuário", "Redefinir Senha de Usuário"]
        admin_action = st.sidebar.selectbox("Gerenciar Usuários", admin_action_options, key="admin_action_sb_v3")
        
        # Para popular selectbox de usuários, busca a lista mais recente do DB
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
            with st.form("form_admin_cadastrar_usuario_v3", clear_on_submit=True):
                reg_name_adm = st.text_input("Nome Completo", key="adm_reg_name_v3")
                reg_uname_adm = st.text_input("Nome de Usuário (login)", key="adm_reg_uname_v3")
                reg_email_adm = st.text_input("Email", key="adm_reg_email_v3")
                reg_pass_adm = st.text_input("Senha", type="password", key="adm_reg_pass_v3")
                reg_role_adm = st.selectbox("Papel", ["user", "admin"], key="adm_reg_role_v3")
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
                user_to_edit_uname = st.selectbox("Usuário a editar", list(current_db_users_info.keys()), key="adm_edit_sel_user_v3")
                if user_to_edit_uname:
                    user_data = current_db_users_info.get(user_to_edit_uname) # Use .get para segurança
                    if user_data:
                        with st.form(f"form_edit_user_{user_to_edit_uname}", key=f"adm_edit_form_{user_to_edit_uname}_v3"):
                            edit_name = st.text_input("Nome", value=user_data.get('name', ''), key=f"adm_edit_name_{user_to_edit_uname}_v3")
                            edit_email = st.text_input("Email", value=user_data.get('email', ''), key=f"adm_edit_email_{user_to_edit_uname}_v3")
                            roles = ["user", "admin"]
                            current_role_idx = roles.index(user_data.get('role', 'user')) if user_data.get('role', 'user') in roles else 0
                            edit_role = st.selectbox("Papel", roles, index=current_role_idx, key=f"adm_edit_role_{user_to_edit_uname}_v3")
                            if st.form_submit_button("Salvar Alterações"):
                                if umdb.update_user_details(user_to_edit_uname, edit_name, edit_email, edit_role):
                                    st.rerun()
                    else:
                        st.error(f"Dados do usuário '{user_to_edit_uname}' não encontrados.")
        
        elif admin_action == "Excluir Usuário":
            st.subheader("Excluir Usuário")
            if not current_db_users_info:
                st.info("Nenhum usuário para excluir.")
            else:
                user_to_delete_uname = st.selectbox("Usuário a excluir", list(current_db_users_info.keys()), key="adm_del_sel_user_v3")
                if user_to_delete_uname:
                    st.warning(f"Confirma a exclusão de '{user_to_delete_uname}'?")
                    if st.button(f"Excluir {user_to_delete_uname}", type="primary", key=f"adm_del_btn_{user_to_delete_uname}_v3"):
                        if umdb.delete_user(user_to_delete_uname):
                            st.rerun()

        elif admin_action == "Redefinir Senha de Usuário":
            st.subheader("Redefinir Senha de Usuário")
            if not current_db_users_info:
                st.info("Nenhum usuário para redefinir senha.")
            else:
                user_to_reset_uname = st.selectbox("Usuário", list(current_db_users_info.keys()), key="adm_reset_sel_user_v3")
                if user_to_reset_uname:
                    with st.form(f"form_reset_pass_{user_to_reset_uname}", clear_on_submit=True, key=f"adm_reset_form_{user_to_reset_uname}_v3"):
                        new_pass = st.text_input("Nova Senha", type="password", key=f"adm_reset_new_pass_{user_to_reset_uname}_v3")
                        confirm_pass = st.text_input("Confirmar Nova Senha", type="password", key=f"adm_reset_conf_pass_{user_to_reset_uname}_v3")
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
    st.write("As páginas específicas do simulador (ex: 'Comandos Rastreadores', 'Simulador PF') "
             "estão disponíveis no menu de navegação da barra lateral após o login.")