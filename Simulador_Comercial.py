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

# --- DEBUG: Verificar se segredos estão carregados ---
# Remova ou comente estas linhas em produção
# st.sidebar.subheader("Debug Secrets")
# if "MONGO_CONNECTION_STRING" in st.secrets:
#     st.sidebar.success("MONGO_CONNECTION_STRING OK")
# else:
#     st.sidebar.error("MONGO_CONNECTION_STRING NÃO ENCONTRADA")
# if "AUTH_COOKIE_NAME" in st.secrets:
#     st.sidebar.success("AUTH_COOKIE_NAME OK")
# else:
#     st.sidebar.error("AUTH_COOKIE_NAME NÃO ENCONTRADA")
# st.sidebar.markdown("---")
# --- FIM DEBUG ---


# --- Carregamento de Usuários e Instância do Autenticador ---
# Esta função agora é robusta a falhas de conexão com o DB
credentials = umdb.fetch_all_users_for_auth()

# Verifica se a conexão com o DB falhou (indicado por credentials vazio e erro de get_mongo_client)
# get_mongo_client já deve ter exibido um erro se a conexão falhou.
# Se credentials estiver vazio, pode ser que não haja usuários ou que a conexão falhou.

authenticator = stauth.Authenticate(
    credentials.get("usernames", {}), # Usa .get para evitar KeyError se 'usernames' não existir
    st.secrets.get("AUTH_COOKIE_NAME", "some_cookie_name"), #Fallback para evitar KeyError
    st.secrets.get("AUTH_COOKIE_KEY", "some_signature_key"), #Fallback
    cookie_expiry_days=st.secrets.get("AUTH_COOKIE_EXPIRY_DAYS", 30), #Fallback
    preauthorized=None # Para permitir que o admin crie usuários
)

# --- Lógica de Login / Registro do Primeiro Admin ---
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
                # Mensagem de erro/sucesso já tratada em umdb.add_user
            else:
                st.warning("Por favor, preencha todos os campos.")
    st.stop()
elif not client_available:
    st.title("Simulador Telemetria")
    st.error("Não foi possível conectar ao banco de dados. Funcionalidades de login e usuário estão indisponíveis.")
    st.info("Verifique as mensagens de erro anteriores ou contate o administrador.")
    st.stop()


# --- Processo de Login ---
name, authentication_status, username = authenticator.login(location='main')

if authentication_status is False:
    st.error("Nome de usuário/senha incorreto(s).")
    st.stop()
elif authentication_status is None:
    st.warning("Por favor, insira seu nome de usuário e senha.")
    st.stop()

# --- Usuário Autenticado ---
if authentication_status:
    # Busca o papel (role) do usuário logado e armazena na sessão
    if "role" not in st.session_state or st.session_state.username != username:
        st.session_state.role = umdb.get_user_role(st.session_state.username)
        if st.session_state.role is None: # Segurança caso não consiga pegar o role
            st.error("Não foi possível determinar o seu nível de acesso. Por favor, faça logout e login novamente.")
            authenticator.logout("Logout", "sidebar")
            st.stop()

    st.sidebar.title(f"Bem-vindo(a), {st.session_state.get('name', username)}!")
    authenticator.logout("Logout", "sidebar")

    # --- Painel do Usuário Comum ---
    if st.session_state.role == "user":
        st.sidebar.subheader("Minha Conta")
        try:
            # Opção para alterar senha (requer senha antiga)
            if authenticator.change_password(username, 'Alterar Senha', location='sidebar'):
                new_hashed_password = authenticator.credentials['usernames'][username]['password']
                if umdb.update_user_password_self(username, new_hashed_password):
                    st.sidebar.success('Senha alterada com sucesso no banco de dados!')
                else:
                    st.sidebar.error('Falha ao salvar a nova senha no banco. Tente novamente.')
                # st.rerun() # O authenticator pode já lidar com o rerun ou estado visual
        except Exception as e:
            st.sidebar.error(f"Erro nas opções de usuário: {e}")
        
        st.sidebar.info("Você tem acesso de visualização aos simuladores.")
        # Aqui o código principal da sua aplicação para usuários normais continua
        # As páginas em `pages/` já farão o controle de acesso.

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
                # Usar st.dataframe para melhor visualização e interatividade
                df_users = pd.DataFrame(all_users_data)
                st.dataframe(df_users, use_container_width=True, hide_index=True)
            else:
                st.info("Nenhum usuário cadastrado (além de você, possivelmente).")

        elif admin_action == "Cadastrar Novo Usuário":
            st.subheader("Cadastrar Novo Usuário")
            with st.form("form_cadastrar_usuario", clear_on_submit=True):
                reg_name = st.text_input("Nome Completo", key="reg_name")
                reg_username = st.text_input("Nome de Usuário (login)", key="reg_uname")
                reg_email = st.text_input("Email", key="reg_email")
                reg_password = st.text_input("Senha", type="password", key="reg_pass")
                reg_role = st.selectbox("Papel (Role)", ["user", "admin"], key="reg_role")
                submit_button = st.form_submit_button("Cadastrar Usuário")

                if submit_button:
                    if reg_name and reg_username and reg_email and reg_password and reg_role:
                        if umdb.add_user(reg_username, reg_name, reg_email, reg_password, reg_role):
                            st.success(f"Usuário {reg_username} adicionado. Recarregando...")
                            st.rerun() # Recarrega para atualizar a lista de usuários e o authenticator
                    else:
                        st.warning("Por favor, preencha todos os campos.")
        
        elif admin_action == "Editar Usuário":
            st.subheader("Editar Usuário")
            users_list_for_edit = [u['username'] for u in credentials.get("usernames", {}).values()]
            if not users_list_for_edit:
                st.info("Nenhum usuário para editar.")
            else:
                selected_user_to_edit = st.selectbox("Selecione o usuário para editar", users_list_for_edit, key="edit_user_select")
                if selected_user_to_edit:
                    # Busca os dados atuais do usuário do 'credentials' que o authenticator usa
                    # Isso é importante porque 'credentials' é o que o authenticator conhece.
                    # Para roles, usamos o que está no DB via fetch_all_users_for_auth
                    user_data_auth = credentials.get("usernames", {}).get(selected_user_to_edit)
                    
                    if user_data_auth:
                        with st.form("form_editar_usuario", key=f"edit_form_{selected_user_to_edit}"):
                            edit_name = st.text_input("Nome Completo", value=user_data_auth.get('name', ''), key=f"edit_name_{selected_user_to_edit}")
                            edit_email = st.text_input("Email", value=user_data_auth.get('email', ''), key=f"edit_email_{selected_user_to_edit}")
                            
                            current_role = user_data_auth.get('role', 'user')
                            role_options = ["user", "admin"]
                            current_role_index = role_options.index(current_role) if current_role in role_options else 0
                            edit_role = st.selectbox("Papel (Role)", role_options, index=current_role_index, key=f"edit_role_{selected_user_to_edit}")
                            
                            submit_edit = st.form_submit_button("Salvar Alterações")

                            if submit_edit:
                                if umdb.update_user_details(selected_user_to_edit, edit_name, edit_email, edit_role):
                                    st.success(f"Usuário {selected_user_to_edit} atualizado. Recarregando...")
                                    st.rerun()
                    else:
                        st.error(f"Dados do usuário '{selected_user_to_edit}' não encontrados para edição.")

        elif admin_action == "Excluir Usuário":
            st.subheader("Excluir Usuário")
            users_list_for_delete = [u['username'] for u in credentials.get("usernames", {}).values()]
            if not users_list_for_delete:
                st.info("Nenhum usuário para excluir.")
            else:
                selected_user_to_delete = st.selectbox("Selecione o usuário para excluir", users_list_for_delete, key="delete_user_select")
                if selected_user_to_delete:
                    st.warning(f"Tem certeza que deseja excluir o usuário '{selected_user_to_delete}'? Esta ação é irreversível.")
                    if st.button(f"Confirmar Exclusão de {selected_user_to_delete}", type="primary", key=f"del_btn_{selected_user_to_delete}"):
                        if umdb.delete_user(selected_user_to_delete):
                            st.success(f"Usuário {selected_user_to_delete} excluído. Recarregando...")
                            st.rerun()
        
        elif admin_action == "Redefinir Senha de Usuário":
            st.subheader("Redefinir Senha de Usuário")
            users_list_for_reset = [u['username'] for u in credentials.get("usernames", {}).values()]
            if not users_list_for_reset:
                st.info("Nenhum usuário disponível.")
            else:
                selected_user_to_reset_pass = st.selectbox("Selecione o usuário", users_list_for_reset, key="reset_pass_select")
                if selected_user_to_reset_pass:
                    with st.form(f"form_reset_senha_{selected_user_to_reset_pass}", clear_on_submit=True):
                        new_plain_password = st.text_input("Nova Senha", type="password", key=f"reset_pass_new_{selected_user_to_reset_pass}")
                        confirm_password = st.text_input("Confirmar Nova Senha", type="password", key=f"reset_pass_confirm_{selected_user_to_reset_pass}")
                        submit_reset = st.form_submit_button("Redefinir Senha")

                        if submit_reset:
                            if not new_plain_password:
                                st.warning("O campo Nova Senha não pode estar vazio.")
                            elif new_plain_password != confirm_password:
                                st.warning("As senhas não coincidem.")
                            else:
                                if umdb.update_user_password_by_admin(selected_user_to_reset_pass, new_plain_password):
                                    st.success(f"Senha para {selected_user_to_reset_pass} redefinida. Recarregando...")
                                    st.rerun()
        
        st.sidebar.info("Você tem acesso total como administrador.")

    # --- Conteúdo Principal do Simulador (Visível para todos os logados) ---
    st.markdown("---")
    st.header("Simulador de Telemetria")
    st.write("Bem-vindo ao sistema! Use o menu na barra lateral para navegar entre as funcionalidades e opções da sua conta.")
    st.write("As páginas específicas do simulador estão disponíveis no menu de navegação que aparece ao expandir a seção de 'Páginas' (se houver páginas na pasta `pages`).")

    # Seu código original da página principal pode vir aqui, se aplicável
    # Ex: st.image("logo.png")
    # st.markdown("## Visão Geral")
    # ...

else:
    # Este bloco só será alcançado se authentication_status for None (antes do login) ou False (falha no login)
    # e o código de parada não tiver sido acionado.
    # A lógica de st.stop() após erros de login geralmente impede que este bloco seja visto.
    if client_available: # Só mostra o formulário de login se o DB estiver teoricamente acessível
        st.info("Aguardando login na tela principal...")
    else:
        # Erro de conexão com o DB já foi mostrado.
        pass