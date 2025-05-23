# Simulador_Comercial.py
import streamlit as st
import streamlit_authenticator as stauth
import pandas as pd

# --- Configuração Inicial da Página ---
st.set_page_config(page_title="Simulador Telemetria", layout="wide")

# --- Importação Segura do Módulo de Banco de Dados ---
try:
    import user_management_db as umdb
except ModuleNotFoundError:
    st.error("ERRO CRÍTICO: O arquivo 'user_management_db.py' não foi encontrado.")
    st.info("Verifique se 'user_management_db.py' está na mesma pasta que 'Simulador_Comercial.py'.")
    st.stop() # Interrompe a execução se o módulo essencial estiver ausente

# --- Carregamento de Credenciais e Verificação da Conexão com DB ---
# A função get_mongo_client() dentro de umdb já tenta conectar e mostra erros.
# Ela é chamada por get_users_collection(), que é chamada por fetch_all_users_for_auth().
print("INFO (Simulador_Comercial.py): Tentando buscar credenciais...")
credentials = umdb.fetch_all_users_for_auth() # Deve retornar {"usernames": {...}}
client_available = umdb.get_mongo_client() is not None # Verifica se o cliente foi obtido com sucesso

# --- DEBUGGING BLOCK (Opcional) ---
# Você pode descomentar este bloco para depurar o que 'credentials' contém.
# st.sidebar.subheader("Debug Info")
# st.sidebar.write("Conexão com DB disponível:", client_available)
# st.sidebar.write("Conteúdo de 'credentials':")
# if isinstance(credentials, dict):
#     st.sidebar.json(credentials)
#     if not credentials.get("usernames"):
#         st.sidebar.warning("Debug: 'credentials[\"usernames\"]' está vazio ou não existe.")
# else:
#     st.sidebar.error(f"Debug: 'credentials' não é um dicionário. Tipo: {type(credentials)}")
# st.sidebar.markdown("---")
# --- END DEBUGGING BLOCK ---

# --- Configuração do Autenticador ---
# Busca chaves de autenticação dos segredos, com fallbacks (idealmente, nunca usados)
auth_cookie_name = st.secrets.get("AUTH_COOKIE_NAME", "simulador_cookie_fallback")
auth_cookie_key = st.secrets.get("AUTH_COOKIE_KEY", "fallback_secret_key_MUDA_ISSO") # Chave secreta é crucial
auth_cookie_expiry_days = st.secrets.get("AUTH_COOKIE_EXPIRY_DAYS", 30)

if "fallback" in auth_cookie_name or "fallback" in auth_cookie_key:
    st.warning("ALERTA DE SEGURANÇA: Chaves de autenticação (AUTH_COOKIE_NAME/AUTH_COOKIE_KEY) "
               "não encontradas em .streamlit/secrets.toml ou usando valores de fallback. "
               "Configure-as corretamente para segurança.")

# Inicializa o autenticador
# A correção do KeyError: 'usernames' foi passar 'credentials' diretamente.
# A correção do TypeError 'preauthorized' foi remover esse argumento.
try:
    authenticator = stauth.Authenticate(
        credentials, # Passa o dicionário completo retornado por fetch_all_users_for_auth
        auth_cookie_name,
        auth_cookie_key,
        cookie_expiry_days=auth_cookie_expiry_days
    )
except Exception as e:
    st.error(f"ERRO AO INICIALIZAR O AUTENTICADOR: {e}")
    st.error("Isso pode ser devido a 'credentials' estar malformado ou um problema com as chaves de cookie.")
    st.info("Verifique o debug de 'credentials' na barra lateral (se descomentado) e as chaves de cookie nos segredos.")
    if isinstance(credentials, dict) and "usernames" not in credentials:
        st.error("Diagnóstico: A chave 'usernames' está faltando no dicionário 'credentials' passado para o Authenticate.")
    st.stop()


# --- Lógica Principal da Aplicação ---

if not client_available:
    # Se a conexão com o DB falhou completamente no início.
    st.title("Simulador Telemetria")
    st.error("FALHA CRÍTICA NA CONEXÃO COM O BANCO DE DADOS.")
    st.info("O sistema de login e as funcionalidades dependentes do banco de dados estão indisponíveis. "
            "Verifique as mensagens de erro no console/logs, o arquivo '.streamlit/secrets.toml', "
            "e as configurações de acesso à rede no MongoDB Atlas.")
    st.stop()

# Se não há usuários E a conexão com o DB está OK, permite criar o primeiro admin.
# A checagem de client_available já foi feita.
if not credentials.get("usernames"): # Se usernames está vazio
    st.title("Bem-vindo ao Simulador Telemetria! 🚀")
    st.subheader("Configuração Inicial: Criar Conta de Administrador")
    with st.form("FormCriarPrimeiroAdmin"):
        admin_name = st.text_input("Nome Completo", key="init_admin_name_f")
        admin_username = st.text_input("Nome de Usuário (login)", key="init_admin_uname_f")
        admin_email = st.text_input("Email", key="init_admin_email_f")
        admin_password = st.text_input("Senha", type="password", key="init_admin_pass_f")
        submit_admin = st.form_submit_button("Criar Administrador")

        if submit_admin:
            if all([admin_name, admin_username, admin_email, admin_password]):
                if umdb.add_user(admin_username, admin_name, admin_email, admin_password, "admin"):
                    st.success("Conta de administrador criada! Por favor, atualize a página (F5) ou clique abaixo.")
                    if st.button("Recarregar para Login", key="btn_reload_login"):
                        st.rerun()
                # Mensagem de erro/sucesso de add_user já é mostrada por umdb.add_user
            else:
                st.warning("Por favor, preencha todos os campos.")
    st.stop() # Para a execução aqui para forçar o F5 ou o botão


# --- Processo de Login ---
name, authentication_status, username = authenticator.login(location='main')

if authentication_status is False:
    st.error("Nome de usuário ou senha incorreto(s). Tente novamente.")
elif authentication_status is None:
    st.info("Por favor, insira seu nome de usuário e senha para acessar o simulador.")
elif authentication_status: # True, login bem-sucedido
    # --- Usuário Autenticado ---
    # Armazena informações do usuário na sessão do Streamlit
    st.session_state.name = name
    st.session_state.username = username
    st.session_state.authentication_status = authentication_status # Redundante, mas para clareza
    
    # Busca e armazena o papel (role) do usuário. Crucial para controle de acesso.
    # É importante buscar o role do DB após o login bem-sucedido.
    st.session_state.role = umdb.get_user_role(username)
    if st.session_state.role is None:
        st.error("ERRO: Não foi possível determinar seu nível de acesso após o login. "
                 "Por favor, faça logout e tente novamente ou contate o suporte.")
        authenticator.logout("Logout (Erro de Role)", "sidebar")
        st.stop()

    # UI Pós-Login
    st.sidebar.title(f"Bem-vindo(a), {name}!")
    authenticator.logout("Logout", "sidebar")

    # --- Painel do Usuário Comum ---
    if st.session_state.role == "user":
        st.sidebar.subheader("Minha Conta")
        try:
            if authenticator.change_password(username, 'Alterar Senha', location='sidebar'):
                new_hashed_pass = authenticator.credentials['usernames'][username]['password']
                if umdb.update_user_password_self(username, new_hashed_pass):
                    st.sidebar.success('Senha alterada com sucesso no banco de dados!')
                else: # Falha ao salvar no DB
                    st.sidebar.error('Falha ao salvar nova senha no banco. Tente novamente.')
        except Exception as e:
            st.sidebar.error(f"Erro ao tentar alterar senha: {e}")
        st.sidebar.info("Você tem acesso de visualização aos simuladores.")

    # --- Painel do Administrador ---
    elif st.session_state.role == "admin":
        st.sidebar.subheader("Painel de Administração")
        admin_action_options = ["Ver Usuários", "Cadastrar Novo Usuário", "Editar Usuário",
                                "Excluir Usuário", "Redefinir Senha de Usuário"]
        admin_action = st.sidebar.selectbox("Gerenciar Usuários", admin_action_options, key="admin_action_sb")

        # Para popular selectbox de usuários, buscamos a lista mais recente
        # A variável 'credentials' pode estar desatualizada se houver adição/remoção sem rerun.
        # É mais seguro buscar do DB para estas operações.
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
                reg_name_adm = st.text_input("Nome Completo", key="adm_reg_name")
                reg_uname_adm = st.text_input("Nome de Usuário (login)", key="adm_reg_uname")
                reg_email_adm = st.text_input("Email", key="adm_reg_email")
                reg_pass_adm = st.text_input("Senha", type="password", key="adm_reg_pass")
                reg_role_adm = st.selectbox("Papel", ["user", "admin"], key="adm_reg_role")
                submit_btn_adm = st.form_submit_button("Cadastrar Usuário")
                if submit_btn_adm:
                    if all([reg_name_adm, reg_uname_adm, reg_email_adm, reg_pass_adm, reg_role_adm]):
                        if umdb.add_user(reg_uname_adm, reg_name_adm, reg_email_adm, reg_pass_adm, reg_role_adm):
                            st.rerun() # Atualiza tudo
                    else:
                        st.warning("Preencha todos os campos para cadastrar.")
        
        # Outras Ações de Admin (Editar, Excluir, Redefinir Senha)
        # Usam current_db_users_info para popular os selectboxes
        
        elif admin_action == "Editar Usuário":
            st.subheader("Editar Usuário")
            if not current_db_users_info:
                st.info("Nenhum usuário para editar.")
            else:
                user_to_edit_uname = st.selectbox("Usuário a editar", list(current_db_users_info.keys()), key="adm_edit_sel_user")
                if user_to_edit_uname:
                    user_data = current_db_users_info[user_to_edit_uname]
                    with st.form(f"form_edit_user_{user_to_edit_uname}", key=f"adm_edit_form_{user_to_edit_uname}"):
                        edit_name = st.text_input("Nome", value=user_data.get('name', ''), key=f"adm_edit_name_{user_to_edit_uname}")
                        edit_email = st.text_input("Email", value=user_data.get('email', ''), key=f"adm_edit_email_{user_to_edit_uname}")
                        roles = ["user", "admin"]
                        current_role_idx = roles.index(user_data.get('role', 'user')) if user_data.get('role', 'user') in roles else 0
                        edit_role = st.selectbox("Papel", roles, index=current_role_idx, key=f"adm_edit_role_{user_to_edit_uname}")
                        if st.form_submit_button("Salvar Alterações"):
                            if umdb.update_user_details(user_to_edit_uname, edit_name, edit_email, edit_role):
                                st.rerun()
        
        elif admin_action == "Excluir Usuário":
            st.subheader("Excluir Usuário")
            if not current_db_users_info:
                st.info("Nenhum usuário para excluir.")
            else:
                user_to_delete_uname = st.selectbox("Usuário a excluir", list(current_db_users_info.keys()), key="adm_del_sel_user")
                if user_to_delete_uname:
                    st.warning(f"Confirma a exclusão de '{user_to_delete_uname}'? Esta ação é irreversível.")
                    if st.button(f"Excluir {user_to_delete_uname}", type="primary", key=f"adm_del_btn_{user_to_delete_uname}"):
                        if umdb.delete_user(user_to_delete_uname):
                            st.rerun()

        elif admin_action == "Redefinir Senha de Usuário":
            st.subheader("Redefinir Senha de Usuário")
            if not current_db_users_info:
                st.info("Nenhum usuário para redefinir senha.")
            else:
                user_to_reset_uname = st.selectbox("Usuário", list(current_db_users_info.keys()), key="adm_reset_sel_user")
                if user_to_reset_uname:
                    with st.form(f"form_reset_pass_{user_to_reset_uname}", clear_on_submit=True, key=f"adm_reset_form_{user_to_reset_uname}"):
                        new_pass = st.text_input("Nova Senha", type="password", key=f"adm_reset_new_pass_{user_to_reset_uname}")
                        confirm_pass = st.text_input("Confirmar Nova Senha", type="password", key=f"adm_reset_conf_pass_{user_to_reset_uname}")
                        if st.form_submit_button("Redefinir Senha"):
                            if not new_pass: st.warning("Senha não pode ser vazia.")
                            elif new_pass != confirm_pass: st.warning("Senhas não coincidem.")
                            else:
                                if umdb.update_user_password_by_admin(user_to_reset_uname, new_pass):
                                    st.rerun()
        st.sidebar.info("Você tem acesso total como administrador.")

    # --- Conteúdo Principal do Simulador ---
    st.markdown("---") # Divisor visual
    st.header("Simulador de Telemetria Principal")
    st.write("Bem-vindo(a)! Navegue pelas funcionalidades usando o menu lateral.")
    st.write("As páginas específicas do simulador (Simulador PF, Simulador PJ, etc.) "
             "estarão disponíveis no menu de navegação 'Pages' se você tiver a estrutura de pastas correta.")
    # Aqui você pode adicionar qualquer conteúdo que deva aparecer na página principal para usuários logados.


# Se authentication_status não for True (ou seja, False ou None),
# as mensagens de erro ou o formulário de login já foram exibidos.
# Nenhuma ação adicional necessária aqui.