# Simulador_Comercial.py
import streamlit as st
import streamlit_authenticator as stauth
import pandas as pd # Apenas para o exemplo de exibir usuários

# Tenta importar o user_management_db. Se falhar, mostra um erro claro e para.
try:
    import user_management_db as umdb
except ModuleNotFoundError:
    st.error("ERRO CRÍTICO: O arquivo 'user_management_db.py' não foi encontrado.")
    st.info("Certifique-se de que 'user_management_db.py' está na mesma pasta que 'Simulador_Comercial.py'.")
    st.stop()


st.set_page_config(page_title="Simulador Telemetria", layout="wide")

# --- Carregamento de Usuários e Instância do Autenticador ---
# Esta função agora é robusta a falhas de conexão com o DB
# Se a conexão com o DB falhar, um erro já terá sido exibido por get_mongo_client()
# e credentials será {"usernames": {}}
credentials = umdb.fetch_all_users_for_auth()

# --- DEBUGGING BLOCK ---
# Este bloco ajuda a ver o que está em 'credentials' antes de passar para o Authenticate
# Você pode comentar ou remover este bloco após o debug.
st.sidebar.subheader("Debug: 'credentials'")
if isinstance(credentials, dict):
    st.sidebar.json(credentials)
    if not credentials.get("usernames"):
        st.sidebar.warning("Debug: 'credentials[usernames]' está vazio ou não existe.")
else:
    st.sidebar.error(f"Debug: 'credentials' não é um dicionário. Tipo: {type(credentials)}")
st.sidebar.markdown("---")
# --- END DEBUGGING BLOCK ---

# Verifica se st.secrets possui as chaves necessárias para o Authenticator
# Define fallbacks para evitar KeyError se as chaves não estiverem nos segredos
# Isso é mais para robustez, o ideal é que as chaves SEMPRE estejam em secrets.toml
auth_cookie_name = st.secrets.get("AUTH_COOKIE_NAME", "simulador_auth_cookie_fallback")
auth_cookie_key = st.secrets.get("AUTH_COOKIE_KEY", "fallback_secret_key_please_change")
auth_cookie_expiry_days = st.secrets.get("AUTH_COOKIE_EXPIRY_DAYS", 30)

if auth_cookie_name == "simulador_auth_cookie_fallback" or auth_cookie_key == "fallback_secret_key_please_change":
    st.warning("ALERTA: Chaves de autenticação (AUTH_COOKIE_NAME/AUTH_COOKIE_KEY) não encontradas em secrets.toml. Usando fallbacks inseguros.")

authenticator = stauth.Authenticate(
    credentials.get("usernames", {}), # Usa .get para segurança, caso 'usernames' não exista em credentials
    auth_cookie_name,
    auth_cookie_key,
    cookie_expiry_days=auth_cookie_expiry_days,
    preauthorized=None # Permite que o admin crie usuários sem preautorização por email
)

# --- Lógica de Login / Registro do Primeiro Admin ---
# Verifica se o cliente MongoDB está disponível (ou seja, se a conexão inicial foi bem-sucedida)
client_available = umdb.get_mongo_client() is not None

if not credentials.get("usernames") and client_available:
    # Se não há usuários E a conexão com o DB está OK, permite criar o primeiro admin
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
                        st.rerun() # st.experimental_rerun em versões mais antigas
                # Mensagens de erro/sucesso durante add_user são tratadas dentro de umdb.add_user
            else:
                st.warning("Por favor, preencha todos os campos.")
    st.stop() # Para a execução aqui para forçar o F5 ou o botão
elif not client_available:
    # Se a conexão com o DB falhou no início, exibe uma mensagem de erro principal
    st.title("Simulador Telemetria")
    st.error("FALHA CRÍTICA: Não foi possível conectar ao banco de dados.")
    st.info("As funcionalidades de login e gerenciamento de usuários estão indisponíveis. Verifique as mensagens de erro no console ou nos logs, e confira a configuração do arquivo '.streamlit/secrets.toml' e o acesso à rede do MongoDB Atlas.")
    st.stop() # Para a execução completamente


# --- Processo de Login ---
# O widget de login é renderizado aqui.
# name, authentication_status, username são preenchidos pelo authenticator.
name, authentication_status, username = authenticator.login(location='main')

if authentication_status is False:
    st.error("Nome de usuário ou senha incorreto(s).")
    # Não precisa de st.stop() aqui, o loop do Streamlit vai re-renderizar.
elif authentication_status is None:
    st.info("Por favor, insira seu nome de usuário e senha para acessar o simulador.")
    # Não precisa de st.stop() aqui.
elif authentication_status: # Equivalente a authentication_status is True
    # --- Usuário Autenticado ---
    # Busca o papel (role) do usuário logado e armazena na sessão
    # Garante que o st.session_state é atualizado se o usuário mudar (improvável sem logout)
    if "role" not in st.session_state or st.session_state.get("username") != username:
        st.session_state.username = username # Garante que o username na sessão é o atual
        st.session_state.name = name # Garante que o nome na sessão é o atual
        st.session_state.role = umdb.get_user_role(username)
        if st.session_state.role is None:
            st.error("Não foi possível determinar o seu nível de acesso. Por favor, faça logout e tente novamente.")
            authenticator.logout("Logout Problemático", "sidebar")
            st.stop()

    st.sidebar.title(f"Bem-vindo(a), {st.session_state.get('name', username)}!")
    authenticator.logout("Logout", "sidebar") # Botão de Logout

    # --- Painel do Usuário Comum ---
    if st.session_state.role == "user":
        st.sidebar.subheader("Minha Conta")
        try:
            if authenticator.change_password(username, 'Alterar Senha', location='sidebar'):
                # Se change_password retornar True, a senha no 'credentials' do authenticator foi atualizada.
                # Precisamos persistir essa nova senha (já hasheada) no banco de dados.
                new_hashed_password = authenticator.credentials['usernames'][username]['password']
                if umdb.update_user_password_self(username, new_hashed_password):
                    st.sidebar.success('Senha alterada com sucesso no banco de dados!')
                else:
                    st.sidebar.error('Falha ao salvar a nova senha no banco. Tente novamente ou contate o suporte.')
                # st.rerun() # O authenticator pode lidar com o estado visual, mas um rerun pode ser bom
        except Exception as e:
            st.sidebar.error(f"Erro ao tentar alterar senha: {e}")

        st.sidebar.info("Você tem acesso de visualização aos simuladores.")
        # O conteúdo principal para usuários comuns virá das páginas na pasta `pages/`

    # --- Painel do Administrador ---
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
                st.info("Nenhum usuário cadastrado (além de você, se for o primeiro).")

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
            # Usamos 'credentials' pois é a fonte que o authenticator conhece e que foi carregada inicialmente
            # Para editar, é importante que a lista de usuários esteja atualizada.
            # Se um usuário for adicionado/removido e um rerun não ocorrer, esta lista pode estar defasada.
            # O st.rerun() após add/delete ajuda a mitigar isso.
            users_for_auth = umdb.fetch_all_users_for_auth().get("usernames", {}) # Busca novamente para ter a lista mais atual
            
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
                                current_role_index = 0 # Default to 'user' if role is unknown
                            
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

    # --- Conteúdo Principal do Simulador (Visível para todos os logados) ---
    st.markdown("---")
    st.header("Simulador de Telemetria")
    st.write("Bem-vindo ao sistema! Use o menu na barra lateral para navegar entre as funcionalidades e opções da sua conta.")
    st.write("As páginas específicas do simulador estão disponíveis no menu de navegação que aparece ao expandir a seção de 'Páginas' (se houver páginas na pasta `pages`).")

    # Seu código original da página principal pode vir aqui, se aplicável
    # Ex: if st.button("Mostrar DataFrame do Simulador"):
    #         if 'df_simulador' not in st.session_state:
    #              st.session_state.df_simulador = pd.DataFrame({ # Exemplo
    #                  'Coluna1': [1, 2, 3],
    #                  'Coluna2': ['A', 'B', 'C']
    #              })
    #         st.dataframe(st.session_state.df_simulador)

# O bloco 'else' para authentication_status não ser True já foi tratado
# pelas condições de authentication_status is False e authentication_status is None.