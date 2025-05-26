# Simulador_Comercial.py
import streamlit as st
import pandas as pd # Certifique-se de que 'pandas' está no seu requirements.txt

# --- Configuração Inicial da Página ---
# Deve ser o primeiro comando Streamlit, exceto imports.
st.set_page_config(page_title="Simulador Telemetria Principal", layout="wide")
print(f"INFO_LOG (Simulador_Comercial.py): Página configurada. Streamlit version: {st.__version__}")

# --- Importação Segura de Módulos Essenciais ---
umdb = None
try:
    import user_management_db as umdb_module
    umdb = umdb_module # Atribui ao alias global se a importação for bem-sucedida
    print("INFO_LOG (Simulador_Comercial.py): Módulo user_management_db importado com sucesso.")
except ModuleNotFoundError:
    st.error("ERRO CRÍTICO: O arquivo 'user_management_db.py' não foi encontrado.")
    st.info("Verifique se 'user_management_db.py' está na mesma pasta que 'Simulador_Comercial.py'.")
    print("CRITICAL_ERROR_LOG (Simulador_Comercial.py): user_management_db.py não encontrado.")
    st.stop() 
except ImportError as ie_umdb:
    st.error(f"ERRO CRÍTICO AO IMPORTAR user_management_db: {ie_umdb}")
    print(f"CRITICAL_IMPORT_ERROR_LOG (Simulador_Comercial.py): user_management_db: {ie_umdb}")
    st.stop()
except Exception as e_umdb_general: # Captura genérica para outros possíveis erros de importação de umdb
    st.error(f"ERRO INESPERADO AO IMPORTAR user_management_db: {e_umdb_general}")
    print(f"UNEXPECTED_IMPORT_ERROR_LOG (Simulador_Comercial.py): user_management_db: {e_umdb_general}")
    st.stop()

stauth = None # Inicializa stauth como None
try:
    import streamlit_authenticator as stauth_module # Importa para uma variável temporária
    stauth = stauth_module # Atribui à variável principal se a importação for bem-sucedida
    print(f"INFO_LOG (Simulador_Comercial.py): streamlit_authenticator importado. Versão: {stauth.__version__}")
except ModuleNotFoundError:
    st.error("ERRO CRÍTICO: A biblioteca 'streamlit-authenticator' não está instalada. Verifique seu 'requirements.txt' e os logs de build do Streamlit Cloud.")
    print("CRITICAL_ERROR_LOG (Simulador_Comercial.py): streamlit-authenticator NÃO ENCONTRADO (ModuleNotFoundError).")
    st.stop()
except ImportError as ie_stauth:
    st.error(f"ERRO CRÍTICO AO IMPORTAR streamlit_authenticator: {ie_stauth}")
    print(f"CRITICAL_IMPORT_ERROR_LOG (Simulador_Comercial.py): streamlit_authenticator (ImportError): {ie_stauth}")
    st.stop()
except Exception as e_stauth_general: # Captura genérica para outros possíveis erros de importação
    st.error(f"ERRO INESPERADO AO IMPORTAR streamlit_authenticator: {e_stauth_general}")
    print(f"UNEXPECTED_IMPORT_ERROR_LOG (Simulador_Comercial.py): streamlit_authenticator (Exception): {e_stauth_general}")
    st.stop()

# Verificação final se os módulos essenciais foram carregados
if umdb is None or stauth is None:
    st.error("ERRO CRÍTICO: Falha ao carregar módulos essenciais (user_management_db ou streamlit_authenticator). O aplicativo não pode continuar.")
    print("CRITICAL_ERROR_LOG (Simulador_Comercial.py): umdb ou stauth permaneceu None após tentativas de importação.")
    if umdb is None:
        print("CRITICAL_ERROR_LOG (Simulador_Comercial.py): umdb é None.")
    if stauth is None:
        print("CRITICAL_ERROR_LOG (Simulador_Comercial.py): stauth é None.")
    st.stop()


# --- Carregamento de Credenciais e Verificação da Conexão com DB ---
print("INFO_LOG (Simulador_Comercial.py): Buscando credenciais do banco de dados...")
credentials = umdb.fetch_all_users_for_auth() 
client_available = umdb.get_mongo_client() is not None 

print(f"DEBUG_LOG (Simulador_Comercial.py): client_available = {client_available}")
print(f"DEBUG_LOG (Simulador_Comercial.py): credentials (tipo: {type(credentials)}) = {credentials}")
if isinstance(credentials, dict) and not credentials.get("usernames"):
    print("DEBUG_LOG (Simulador_Comercial.py): 'credentials[\"usernames\"]' está vazio ou não existe (pode ser normal se o DB estiver vazio ou a conexão falhou).")


# --- Configuração do Autenticador ---
auth_cookie_name = st.secrets.get("AUTH_COOKIE_NAME")
auth_cookie_key = st.secrets.get("AUTH_COOKIE_KEY")
auth_cookie_expiry_days = st.secrets.get("AUTH_COOKIE_EXPIRY_DAYS", 30) 

if not auth_cookie_name or not auth_cookie_key:
    st.error("ERRO DE CONFIGURAÇÃO CRÍTICO: AUTH_COOKIE_NAME ou AUTH_COOKIE_KEY não definidos nos segredos do Streamlit Cloud.")
    print("CRITICAL_ERROR_LOG (Simulador_Comercial.py): AUTH_COOKIE_NAME ou AUTH_COOKIE_KEY não encontrados nos segredos.")
    st.info("Adicione-os nas configurações de 'Secrets' do seu app no Streamlit Cloud. O aplicativo não pode continuar de forma segura.")
    st.stop()

try:
    print(f"INFO_LOG (Simulador_Comercial.py): Inicializando Authenticator com credentials: {credentials}")
    authenticator = stauth.Authenticate(
        credentials, 
        auth_cookie_name,
        auth_cookie_key,
        cookie_expiry_days=auth_cookie_expiry_days
    )
    print("INFO_LOG (Simulador_Comercial.py): Autenticador inicializado com sucesso.")
except Exception as e_auth_init:
    st.error(f"ERRO CRÍTICO AO INICIALIZAR O AUTENTICADOR: {e_auth_init}")
    print(f"AUTHENTICATOR_INIT_ERROR_LOG (Simulador_Comercial.py): {e_auth_init}")
    print(f"AUTHENTICATOR_INIT_ERROR_LOG (Simulador_Comercial.py): Tipo de credentials: {type(credentials)}")
    print(f"AUTHENTICATOR_INIT_ERROR_LOG (Simulador_Comercial.py): Conteúdo de credentials: {credentials}")
    st.stop()

# --- Lógica Principal da Aplicação ---

if not client_available:
    st.title("Simulador Telemetria")
    st.error("FALHA CRÍTICA NA CONEXÃO COM O BANCO DE DADOS.")
    st.info("O sistema de login e as funcionalidades dependentes estão indisponíveis. "
            "Verifique os logs do aplicativo no Streamlit Cloud para mensagens de erro de 'user_management_db.py', "
            "especialmente sobre MONGO_CONNECTION_STRING e acesso à rede do MongoDB Atlas.")
    print("CRITICAL_ERROR_LOG (Simulador_Comercial.py): client_available é False. Parando execução.")
    st.stop()

if not credentials.get("usernames"): 
    st.title("Bem-vindo ao Simulador Telemetria! 🚀")
    st.subheader("Configuração Inicial: Criar Conta de Administrador")
    print("INFO_LOG (Simulador_Comercial.py): Nenhum usuário no DB (ou falha ao buscar). Exibindo formulário de criação do primeiro admin.")
    with st.form("FormCriarPrimeiroAdmin_v5"): # Chave do formulário atualizada
        admin_name = st.text_input("Nome Completo", key="init_admin_name_v5")
        admin_username = st.text_input("Nome de Usuário (login)", key="init_admin_uname_v5")
        admin_email = st.text_input("Email", key="init_admin_email_v5")
        admin_password = st.text_input("Senha", type="password", key="init_admin_pass_v5")
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
print(f"DEBUG_LOG (Simulador_Comercial.py): st.session_state ANTES do login: {st.session_state.to_dict()}")


name, authentication_status, username = None, None, None 
login_attempted_flag = False 

try:
    login_return_value = authenticator.login(location='main')
    login_attempted_flag = True 

    print(f"DEBUG_LOG (Simulador_Comercial.py): authenticator.login() retornou: {login_return_value} (Tipo: {type(login_return_value)})")

    if login_return_value is not None and isinstance(login_return_value, tuple) and len(login_return_value) == 3:
        name, authentication_status, username = login_return_value
    elif login_return_value is None:
        print("WARN_LOG (Simulador_Comercial.py): authenticator.login() retornou None. Investigar.")
        authentication_status = None 
    else: 
        st.error(f"ERRO INESPERADO NO LOGIN: authenticator.login() retornou: {login_return_value}")
        print(f"UNEXPECTED_LOGIN_RETURN_ERROR_LOG (Simulador_Comercial.py): Valor: {login_return_value}")
        st.stop()

except Exception as e_login:
    st.error(f"ERRO CRÍTICO DURANTE authenticator.login(): {e_login}")
    print(f"CRITICAL_AUTHENTICATOR_LOGIN_ERROR_LOG (Simulador_Comercial.py): Exception: {e_login}")
    print(f"DEBUG_LOG (Simulador_Comercial.py): st.session_state no momento da exceção: {st.session_state.to_dict()}")
    st.stop()

print(f"INFO_LOG (Simulador_Comercial.py): Após authenticator.login() - Auth_Status: {authentication_status}, Username: {username}, Name: {name}")

if authentication_status is False:
    st.error("Nome de usuário ou senha incorreto(s). Tente novamente.")
elif authentication_status is None:
    if login_attempted_flag and login_return_value is None:
        st.warning("Ocorreu um problema ao processar o login. Verifique os logs do aplicativo no Streamlit Cloud e tente novamente.")
        st.info("Causas comuns: falha na conexão com o banco de dados ou problema com cookies.")
    else: 
        st.info("Por favor, insira seu nome de usuário e senha.")
elif authentication_status: # True, login bem-sucedido
    st.session_state.name = name
    st.session_state.username = username
    st.session_state.authentication_status = authentication_status
    
    st.session_state.role = umdb.get_user_role(username)
    if st.session_state.role is None:
        st.error("ERRO PÓS-LOGIN: Não foi possível determinar seu nível de acesso.")
        print(f"ERROR_LOG (Simulador_Comercial.py): Falha ao obter role para '{username}'.")
        authenticator.logout("Logout (Erro de Role)", "sidebar")
        st.stop()
    print(f"INFO_LOG (Simulador_Comercial.py): Usuário '{username}' logado. Role: '{st.session_state.role}'.")

    st.sidebar.title(f"Bem-vindo(a), {name}!")
    authenticator.logout("Logout", "sidebar")

    # --- SEÇÕES DE USUÁRIO E ADMIN ---
    if st.session_state.role == "user":
        st.sidebar.subheader("Minha Conta")
        try:
            if authenticator.change_password(username, 'Alterar Senha', location='sidebar'):
                new_hashed_pass = authenticator.credentials['usernames'][username]['password'] # Pega o novo hash do authenticator
                if umdb.update_user_password_self(username, new_hashed_pass):
                    st.sidebar.success('Senha alterada com sucesso!')
                else:
                    st.sidebar.error('Falha ao salvar nova senha no banco.')
        except Exception as e_change_pass:
            st.sidebar.error(f"Erro ao tentar alterar senha: {e_change_pass}")
            print(f"CHANGE_PASSWORD_ERROR_LOG (Simulador_Comercial.py): User '{username}', {e_change_pass}")
        st.sidebar.info("Acesso de visualização aos simuladores.")

    elif st.session_state.role == "admin":
        st.sidebar.subheader("Painel de Administração")
        admin_action_options = ["Ver Usuários", "Cadastrar Novo Usuário", "Editar Usuário",
                                "Excluir Usuário", "Redefinir Senha de Usuário"]
        admin_action = st.sidebar.selectbox("Gerenciar Usuários", admin_action_options, key="admin_action_sb_v5")
        
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
            with st.form("form_admin_cadastrar_usuario_v5", clear_on_submit=True):
                reg_name_adm = st.text_input("Nome Completo", key="adm_reg_name_v5")
                reg_uname_adm = st.text_input("Nome de Usuário (login)", key="adm_reg_uname_v5")
                reg_email_adm = st.text_input("Email", key="adm_reg_email_v5")
                reg_pass_adm = st.text_input("Senha", type="password", key="adm_reg_pass_v5")
                reg_role_adm = st.selectbox("Papel", ["user", "admin"], key="adm_reg_role_v5")
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
                user_to_edit_uname = st.selectbox("Usuário a editar", list(current_db_users_info.keys()), key="adm_edit_sel_user_v5")
                if user_to_edit_uname:
                    user_data = current_db_users_info.get(user_to_edit_uname) 
                    if user_data:
                        with st.form(f"form_edit_user_{user_to_edit_uname}", key=f"adm_edit_form_{user_to_edit_uname}_v5"):
                            edit_name = st.text_input("Nome", value=user_data.get('name', ''), key=f"adm_edit_name_{user_to_edit_uname}_v5")
                            edit_email = st.text_input("Email", value=user_data.get('email', ''), key=f"adm_edit_email_{user_to_edit_uname}_v5")
                            roles = ["user", "admin"]
                            current_role_idx = roles.index(user_data.get('role', 'user')) if user_data.get('role', 'user') in roles else 0
                            edit_role = st.selectbox("Papel", roles, index=current_role_idx, key=f"adm_edit_role_{user_to_edit_uname}_v5")
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
                user_to_delete_uname = st.selectbox("Usuário a excluir", list(current_db_users_info.keys()), key="adm_del_sel_user_v5")
                if user_to_delete_uname:
                    st.warning(f"Confirma a exclusão de '{user_to_delete_uname}'?")
                    if st.button(f"Excluir {user_to_delete_uname}", type="primary", key=f"adm_del_btn_{user_to_delete_uname}_v5"):
                        if umdb.delete_user(user_to_delete_uname):
                            st.rerun()

        elif admin_action == "Redefinir Senha de Usuário":
            st.subheader("Redefinir Senha de Usuário")
            if not current_db_users_info:
                st.info("Nenhum usuário para redefinir senha.")
            else:
                user_to_reset_uname = st.selectbox("Usuário", list(current_db_users_info.keys()), key="adm_reset_sel_user_v5")
                if user_to_reset_uname:
                    with st.form(f"form_reset_pass_{user_to_reset_uname}", clear_on_submit=True, key=f"adm_reset_form_{user_to_reset_uname}_v5"):
                        new_pass = st.text_input("Nova Senha", type="password", key=f"adm_reset_new_pass_{user_to_reset_uname}_v5")
                        confirm_pass = st.text_input("Confirmar Nova Senha", type="password", key=f"adm_reset_conf_pass_{user_to_reset_uname}_v5")
                        if st.form_submit_button("Redefinir Senha"):
                            if not new_pass: st.warning("Senha não pode ser vazia.")
                            elif new_pass != confirm_pass: st.warning("Senhas não coincidem.")
                            else:
                                if umdb.update_user_password_by_admin(user_to_reset_uname, new_pass):
                                    st.rerun()
        st.sidebar.info("Acesso de administrador.")

    # --- Conteúdo Principal da Página Pós-Login ---
    st.markdown("---") 
    st.header("Simulador de Telemetria Principal")
    st.write("Navegue pelas funcionalidades usando o menu lateral.")
    st.write("As páginas específicas do simulador estarão disponíveis no menu de navegação da barra lateral (geralmente rotulado como 'Pages' ou com os nomes dos arquivos).")