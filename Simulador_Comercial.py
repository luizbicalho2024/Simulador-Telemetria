# Simulador_Comercial.py
import streamlit as st
import pandas as pd

# --- Configuração Inicial da Página ---
st.set_page_config(page_title="Simulador Telemetria Principal", layout="wide")
print(f"INFO_LOG (Simulador_Comercial.py): Página configurada. Streamlit version: {st.__version__}")

# --- Importação Segura de Módulos Essenciais ---
umdb = None 
try:
    import user_management_db as umdb_module
    umdb = umdb_module 
    print("INFO_LOG (Simulador_Comercial.py): Módulo user_management_db importado.")
except ModuleNotFoundError:
    st.error("ERRO CRÍTICO: 'user_management_db.py' não encontrado.")
    print("CRITICAL_ERROR_LOG (Simulador_Comercial.py): user_management_db.py não encontrado.")
    st.stop() 
except ImportError as ie_umdb:
    st.error(f"ERRO CRÍTICO AO IMPORTAR user_management_db: {ie_umdb}")
    print(f"CRITICAL_IMPORT_ERROR_LOG (Simulador_Comercial.py): user_management_db: {ie_umdb}")
    st.stop()
except Exception as e_umdb_general: 
    st.error(f"ERRO INESPERADO AO IMPORTAR user_management_db: {e_umdb_general}")
    print(f"UNEXPECTED_IMPORT_ERROR_LOG (Simulador_Comercial.py): user_management_db: {e_umdb_general}")
    st.stop()

stauth = None 
try:
    import streamlit_authenticator as stauth_module 
    stauth = stauth_module 
    if hasattr(stauth, '__version__'):
        print(f"INFO_LOG (Simulador_Comercial.py): streamlit_authenticator importado. Versão: {stauth.__version__}")
    else:
        print(f"INFO_LOG (Simulador_Comercial.py): streamlit_authenticator importado, mas sem atributo __version__.")
except ModuleNotFoundError:
    st.error("ERRO CRÍTICO: 'streamlit-authenticator' não instalado. Verifique requirements.txt e logs de build.")
    print("CRITICAL_ERROR_LOG (Simulador_Comercial.py): streamlit-authenticator NÃO ENCONTRADO.")
    st.stop()
except ImportError as ie_stauth:
    st.error(f"ERRO CRÍTICO AO IMPORTAR streamlit_authenticator: {ie_stauth}")
    print(f"CRITICAL_IMPORT_ERROR_LOG (Simulador_Comercial.py): streamlit_authenticator (ImportError): {ie_stauth}")
    st.stop()
except Exception as e_stauth_general: 
    st.error(f"ERRO INESPERADO AO IMPORTAR streamlit_authenticator: {e_stauth_general}")
    print(f"UNEXPECTED_IMPORT_ERROR_LOG (Simulador_Comercial.py): streamlit_authenticator (Exception): {e_stauth_general}")
    st.stop()

if umdb is None or stauth is None:
    st.error("ERRO CRÍTICO: Falha ao carregar módulos essenciais. App não pode continuar.")
    print("CRITICAL_ERROR_LOG (Simulador_Comercial.py): umdb ou stauth é None.")
    st.stop()


# --- Carregamento de Credenciais e Configuração do Autenticador ---
print("INFO_LOG (Simulador_Comercial.py): Buscando credenciais...")
credentials = umdb.fetch_all_users_for_auth() 
client_available = umdb.get_mongo_client() is not None 

print(f"DEBUG_LOG (Simulador_Comercial.py): client_available = {client_available}")
print(f"DEBUG_LOG (Simulador_Comercial.py): credentials (tipo: {type(credentials)}) = {credentials}")

auth_cookie_name = st.secrets.get("AUTH_COOKIE_NAME")
auth_cookie_key = st.secrets.get("AUTH_COOKIE_KEY")
auth_cookie_expiry_days = st.secrets.get("AUTH_COOKIE_EXPIRY_DAYS", 30) 

if not auth_cookie_name or not auth_cookie_key:
    st.error("ERRO DE CONFIGURAÇÃO CRÍTICO: Chaves de cookie não definidas nos segredos.")
    print("CRITICAL_ERROR_LOG (Simulador_Comercial.py): Chaves de cookie ausentes.")
    st.stop()

try:
    print(f"INFO_LOG (Simulador_Comercial.py): Inicializando Authenticator...")
    authenticator = stauth.Authenticate(
        credentials, auth_cookie_name, auth_cookie_key, cookie_expiry_days=auth_cookie_expiry_days
    )
    print("INFO_LOG (Simulador_Comercial.py): Autenticador inicializado.")
except Exception as e_auth_init:
    st.error(f"ERRO CRÍTICO AO INICIALIZAR O AUTENTICADOR: {e_auth_init}")
    print(f"AUTHENTICATOR_INIT_ERROR_LOG (Simulador_Comercial.py): {e_auth_init}, Credentials: {credentials}")
    st.stop()

# --- Lógica Principal ---
if not client_available:
    st.title("Simulador Telemetria")
    st.error("FALHA CRÍTICA NA CONEXÃO COM O BANCO DE DADOS.")
    print("CRITICAL_ERROR_LOG (Simulador_Comercial.py): client_available é False. Parando.")
    st.stop()

if not credentials.get("usernames"): 
    st.title("Bem-vindo ao Simulador Telemetria! 🚀")
    st.subheader("Configuração Inicial: Criar Conta de Administrador")
    print("INFO_LOG (Simulador_Comercial.py): Nenhum usuário. Exibindo formulário de criação do primeiro admin.")
    with st.form("FormCriarPrimeiroAdmin_v10"): # Chave do formulário atualizada
        admin_name = st.text_input("Nome Completo", key="init_admin_name_v10")
        admin_username = st.text_input("Nome de Usuário (login)", key="init_admin_uname_v10")
        admin_email = st.text_input("Email", key="init_admin_email_v10")
        admin_password = st.text_input("Senha", type="password", key="init_admin_pass_v10")
        submit_admin = st.form_submit_button("Criar Administrador")
        if submit_admin:
            if all([admin_name, admin_username, admin_email, admin_password]):
                if umdb.add_user(admin_username, admin_name, admin_email, admin_password, "admin"):
                    st.success("Conta de administrador criada! Recarregando...")
                    print(f"INFO_LOG (Simulador_Comercial.py): Primeiro admin '{admin_username}' criado.")
                    st.rerun()
            else: st.warning("Preencha todos os campos.")
    st.stop() 

# --- Processo de Login ---
print("INFO_LOG (Simulador_Comercial.py): Chamando authenticator.login()...")
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
        print("WARN_LOG (Simulador_Comercial.py): authenticator.login() retornou None.")
        authentication_status = None 
    else: 
        st.error(f"ERRO INESPERADO NO LOGIN: Retorno malformado: {login_return_value}")
        print(f"UNEXPECTED_LOGIN_RETURN_ERROR_LOG (Simulador_Comercial.py): Valor: {login_return_value}")
        st.stop()
except Exception as e_login:
    st.error(f"ERRO CRÍTICO DURANTE authenticator.login(): {e_login}")
    print(f"CRITICAL_AUTHENTICATOR_LOGIN_ERROR_LOG (Simulador_Comercial.py): Exception: {e_login}")
    print(f"DEBUG_LOG (Simulador_Comercial.py): st.session_state na exceção: {st.session_state.to_dict()}")
    st.stop()

print(f"INFO_LOG (Simulador_Comercial.py): Pós login - Status: {authentication_status}, User: {username}")

if authentication_status is False:
    st.error("Nome de usuário ou senha incorreto(s).")
elif authentication_status is None:
    if login_attempted_flag and login_return_value is None:
        st.warning("Ocorreu um problema ao processar o login. Verifique os logs e tente novamente.")
    else: 
        st.info("Por favor, insira seu nome de usuário e senha.")
elif authentication_status: 
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

    if st.session_state.role == "user":
        st.sidebar.subheader("Minha Conta")
        try:
            if authenticator.change_password(username, 'Alterar Senha', location='sidebar'):
                new_hashed_pass = authenticator.credentials['usernames'][username]['password'] 
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
        admin_action = st.sidebar.selectbox("Gerenciar Usuários", admin_action_options, key="admin_action_sb_v10")
        
        # Busca a informação mais recente dos usuários do DB para o painel admin
        current_db_users_dict = umdb.fetch_all_users_for_auth().get("usernames", {})
        
        if admin_action == "Ver Usuários":
            st.subheader("Usuários Cadastrados")
            users_for_display = umdb.get_all_users_for_admin_display()
            if users_for_display:
                df_users = pd.DataFrame(users_for_display)
                st.dataframe(df_users, use_container_width=True, hide_index=True)
            else:
                st.info("Nenhum usuário cadastrado.")

        elif admin_action == "Cadastrar Novo Usuário":
            st.subheader("Cadastrar Novo Usuário")
            with st.form("form_admin_cadastrar_usuario_v10", clear_on_submit=True):
                reg_name_adm = st.text_input("Nome Completo", key="adm_reg_name_v10")
                reg_uname_adm = st.text_input("Nome de Usuário (login)", key="adm_reg_uname_v10")
                reg_email_adm = st.text_input("Email", key="adm_reg_email_v10")
                reg_pass_adm = st.text_input("Senha", type="password", key="adm_reg_pass_v10")
                reg_role_adm = st.selectbox("Papel", ["user", "admin"], key="adm_reg_role_v10")
                if st.form_submit_button("Cadastrar Usuário"):
                    if all([reg_name_adm, reg_uname_adm, reg_email_adm, reg_pass_adm, reg_role_adm]):
                        if umdb.add_user(reg_uname_adm, reg_name_adm, reg_email_adm, reg_pass_adm, reg_role_adm):
                            st.rerun() 
                    else:
                        st.warning("Preencha todos os campos.")
        
        elif admin_action == "Editar Usuário":
            st.subheader("⚙️ Editar Usuário")
            if not current_db_users_dict:
                st.info("Nenhum usuário disponível para edição.")
            else:
                usernames_list_edit = list(current_db_users_dict.keys())
                user_to_edit_uname = st.selectbox("Usuário a editar:", usernames_list_edit, key="adm_edit_sel_user_v10")
                
                if user_to_edit_uname:
                    user_data_for_form = current_db_users_dict.get(user_to_edit_uname)
                    if user_data_for_form:
                        # CORREÇÃO: Usar a chave única do formulário como primeiro argumento posicional.
                        # clear_on_submit=False é o padrão, mas explícito para clareza.
                        with st.form(key=f"form_edit_user_{user_to_edit_uname}_v10", clear_on_submit=False): 
                            st.write(f"Editando dados para: **{user_to_edit_uname}**")
                            edit_name = st.text_input("Nome Completo:", value=user_data_for_form.get('name', ''), key=f"adm_edit_name_val_{user_to_edit_uname}_v10")
                            edit_email = st.text_input("Email:", value=user_data_for_form.get('email', ''), key=f"adm_edit_email_val_{user_to_edit_uname}_v10")
                            
                            roles_options = ["user", "admin"]
                            current_role = user_data_for_form.get('role', 'user')
                            try:
                                current_role_idx_edit = roles_options.index(current_role)
                            except ValueError: 
                                current_role_idx_edit = 0 
                            
                            edit_role = st.selectbox("Novo Papel:", roles_options, index=current_role_idx_edit, key=f"adm_edit_role_val_{user_to_edit_uname}_v10")
                            
                            if st.form_submit_button("Salvar Alterações"):
                                print(f"INFO_LOG (Simulador_Comercial.py - Admin Editar): Tentando editar '{user_to_edit_uname}'")
                                if umdb.update_user_details(user_to_edit_uname, edit_name, edit_email, edit_role):
                                    st.rerun() 
                    else:
                        st.error(f"Não foi possível carregar os dados do usuário '{user_to_edit_uname}'.")
                        print(f"ERROR_LOG (Simulador_Comercial.py - Admin Editar): Dados para '{user_to_edit_uname}' não encontrados.")
        
        elif admin_action == "Redefinir Senha de Usuário":
            st.subheader("🔑 Redefinir Senha de Usuário")
            if not current_db_users_dict:
                st.info("Nenhum usuário disponível para redefinir senha.")
            else:
                usernames_list_reset = list(current_db_users_dict.keys())
                user_to_reset_uname = st.selectbox("Usuário:", usernames_list_reset, key="adm_reset_sel_user_v10")
                
                if user_to_reset_uname:
                    # CORREÇÃO: Usar a chave única do formulário como primeiro argumento posicional.
                    with st.form(key=f"form_reset_pass_{user_to_reset_uname}_v10", clear_on_submit=True):
                        st.write(f"Redefinindo senha para: **{user_to_reset_uname}**")
                        new_pass = st.text_input("Nova Senha:", type="password", key=f"adm_reset_new_pass_{user_to_reset_uname}_v10")
                        confirm_pass = st.text_input("Confirmar Nova Senha:", type="password", key=f"adm_reset_conf_pass_{user_to_reset_uname}_v10")
                        
                        if st.form_submit_button("Redefinir Senha"):
                            print(f"INFO_LOG (Simulador_Comercial.py - Admin Redefinir Senha): Tentativa para '{user_to_reset_uname}'.")
                            if not new_pass: 
                                st.warning("O campo 'Nova Senha' não pode ser vazio.")
                            elif new_pass != confirm_pass: 
                                st.warning("As senhas não coincidem.")
                            else:
                                if umdb.update_user_password_by_admin(user_to_reset_uname, new_pass):
                                    st.rerun() 
                        
        elif admin_action == "Excluir Usuário": 
            st.subheader("🗑️ Excluir Usuário")
            if not current_db_users_dict:
                st.info("Nenhum usuário para excluir.")
            else:
                user_to_delete_uname = st.selectbox("Usuário a excluir:", list(current_db_users_dict.keys()), key="adm_del_sel_user_v10")
                if user_to_delete_uname:
                    st.warning(f"Confirma a exclusão de '{user_to_delete_uname}'?")
                    if st.button(f"Excluir {user_to_delete_uname}", type="primary", key=f"adm_del_btn_{user_to_delete_uname}_v10"):
                        print(f"INFO_LOG (Simulador_Comercial.py - Admin Excluir): Tentativa de excluir '{user_to_delete_uname}'.")
                        if umdb.delete_user(user_to_delete_uname):
                            st.rerun()
        st.sidebar.info("Acesso de administrador.")

    # --- Conteúdo Principal da Página Pós-Login ---
    st.markdown("---") 
    st.header("Simulador de Telemetria Principal")
    st.write("Navegue pelas funcionalidades usando o menu lateral.")
    st.write("As páginas específicas do simulador estarão disponíveis no menu de navegação da barra lateral.")