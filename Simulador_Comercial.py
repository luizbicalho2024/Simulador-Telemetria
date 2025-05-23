# Simulador_Comercial.py (ou seu arquivo principal)
import streamlit as st

# --- LINHA DE TESTE (REMOVER DEPOIS) ---
try:
    mongo_uri_test = st.secrets["MONGO_CONNECTION_STRING"]
    st.sidebar.success(f"Segredo MONGO_CONNECTION_STRING encontrado!") # Remova ou comente esta linha em produção
    # st.sidebar.text(mongo_uri_test) # CUIDADO: Não mostre a string completa em produção
except KeyError:
    st.sidebar.error("ERRO CRÍTICO: Segredo MONGO_CONNECTION_STRING NÃO encontrado em st.secrets!")
    st.stop() # Para a execução se o segredo não for encontrado
# --- FIM DA LINHA DE TESTE ---

import streamlit_authenticator as stauth
import user_management_db as umdb # Nosso módulo de gerenciamento de usuários
import pandas as pd # Exemplo, se você usa pandas


# --- Configuração Inicial e Carregamento de Usuários ---
# Carrega as credenciais do banco de dados
credentials = umdb.fetch_all_users_for_auth()

# Instancia o autenticador
authenticator = stauth.Authenticate(
    credentials,
    st.secrets["AUTH_COOKIE_NAME"],
    st.secrets["AUTH_COOKIE_KEY"],
    st.secrets["AUTH_COOKIE_EXPIRY_DAYS"],
    # Adicione aqui preauthorized se quiser permitir registro por email (não é nosso caso primário)
)

# --- Lógica de Login / Registro do Primeiro Admin ---
# Verifica se existe algum usuário no banco. Se não, permite o registro do primeiro admin.
if not credentials["usernames"]:
    st.title("Bem-vindo ao Simulador! 🚀")
    st.subheader("Configuração Inicial: Criar Conta de Administrador")
    with st.form("Criar Primeiro Admin"):
        admin_name = st.text_input("Nome Completo")
        admin_username = st.text_input("Nome de Usuário (para login)")
        admin_email = st.text_input("Email")
        admin_password = st.text_input("Senha", type="password")
        submit_admin = st.form_submit_button("Criar Administrador")

        if submit_admin:
            if admin_name and admin_username and admin_email and admin_password:
                if umdb.add_user(admin_username, admin_name, admin_email, admin_password, "admin"):
                    st.success("Conta de administrador criada! Por favor, atualize a página para fazer login.")
                    st.rerun() # Recarrega a aplicação para que o authenticator pegue o novo usuário
                else:
                    st.error("Não foi possível criar a conta de administrador.")
            else:
                st.warning("Por favor, preencha todos os campos.")
    st.stop() # Para a execução até que o admin seja criado


# --- Processo de Login ---
# O nome, status de autenticação e nome de usuário são armazenados em st.session_state
# após o login via authenticator.login()
# Exemplo: st.session_state["name"], st.session_state["authentication_status"], st.session_state["username"]

name, authentication_status, username = authenticator.login(location='main') # 'main' ou 'sidebar'

if authentication_status is False:
    st.error("Nome de usuário/senha incorreto")
    st.stop()
elif authentication_status is None:
    st.warning("Por favor, insira seu nome de usuário e senha")
    st.stop()

# --- Usuário Autenticado ---
if authentication_status:
    # Busca o papel (role) do usuário logado e armazena na sessão
    if "role" not in st.session_state or st.session_state.username != username: # Garante que o role é do usuário atual
        st.session_state.role = umdb.get_user_role(st.session_state.username)

    st.sidebar.title(f"Bem-vindo, {st.session_state['name']} 👋")
    authenticator.logout("Logout", "sidebar")

    # --- Painel do Usuário Comum ---
    if st.session_state.role == "user":
        st.sidebar.subheader("Minha Conta")
        try:
            if authenticator.update_user_details(st.session_state.username, 'Atualizar Meus Detalhes', location='sidebar'):
                st.sidebar.success('Detalhes atualizados com sucesso!')
                # Nota: streamlit-authenticator não atualiza o email/nome no backend por padrão com este método.
                # Se quiser permitir que o usuário edite nome/email, precisará de um form customizado
                # que chame umdb.update_user_details e depois st.rerun()
                st.rerun()


            # Alterar Senha para Usuário Logado
            # O authenticator.change_password já lida com o formulário e a lógica de confirmação
            if authenticator.change_password(st.session_state.username, 'Alterar Senha', location='sidebar'):
                new_hashed_password = authenticator.credentials['usernames'][st.session_state.username]['password']
                umdb.update_user_password_self(st.session_state.username, new_hashed_password)
                st.sidebar.success('Senha alterada com sucesso!')
                st.rerun() # Para garantir que tudo é recarregado com as novas credenciais

        except Exception as e:
            st.sidebar.error(f"Erro nas opções de usuário: {e}")

        st.sidebar.info("Você tem acesso de visualização aos simuladores.")
        # Aqui o código principal da sua aplicação para usuários normais continua
        # st.title("Simulador Comercial - Visão Usuário")
        # ... seu código de simulador ... (as páginas em `pages/` já farão o controle)


    # --- Painel do Administrador ---
    elif st.session_state.role == "admin":
        st.sidebar.subheader("Painel de Administração")

        admin_action = st.sidebar.selectbox("Gerenciar Usuários",
                                            ["Ver Usuários", "Cadastrar Novo Usuário", "Editar Usuário",
                                             "Excluir Usuário", "Redefinir Senha de Usuário"])

        if admin_action == "Ver Usuários":
            st.subheader("Usuários Cadastrados")
            all_users_data = umdb.get_all_usernames_and_roles()
            if all_users_data:
                df_users = pd.DataFrame(all_users_data)
                st.dataframe(df_users, use_container_width=True)
            else:
                st.info("Nenhum usuário cadastrado (além de você, possivelmente).")

        elif admin_action == "Cadastrar Novo Usuário":
            st.subheader("Cadastrar Novo Usuário")
            with st.form("form_cadastrar_usuario", clear_on_submit=True):
                new_name = st.text_input("Nome Completo")
                new_username = st.text_input("Nome de Usuário (para login)")
                new_email = st.text_input("Email")
                new_password = st.text_input("Senha", type="password")
                new_role = st.selectbox("Papel (Role)", ["user", "admin"])
                submit_button = st.form_submit_button("Cadastrar Usuário")

                if submit_button:
                    if new_name and new_username and new_email and new_password and new_role:
                        if umdb.add_user(new_username, new_name, new_email, new_password, new_role):
                            st.rerun() # Recarrega para atualizar a lista de usuários e o authenticator
                        # Mensagens de erro/sucesso são tratadas em umdb.add_user
                    else:
                        st.warning("Por favor, preencha todos os campos.")

        elif admin_action == "Editar Usuário":
            st.subheader("Editar Usuário")
            users_list = [u['username'] for u in umdb.get_all_usernames_and_roles()]
            if not users_list:
                st.info("Nenhum usuário para editar.")
            else:
                selected_user_to_edit = st.selectbox("Selecione o usuário para editar", users_list)
                if selected_user_to_edit:
                    user_data = authenticator.credentials['usernames'].get(selected_user_to_edit) # Pega dados atuais
                    if user_data:
                        with st.form("form_editar_usuario"):
                            edit_name = st.text_input("Nome Completo", value=user_data.get('name', ''))
                            edit_email = st.text_input("Email", value=user_data.get('email', ''))
                            current_role_index = 0 if user_data.get('role', 'user') == 'user' else 1
                            edit_role = st.selectbox("Papel (Role)", ["user", "admin"], index=current_role_index)
                            submit_edit = st.form_submit_button("Salvar Alterações")

                            if submit_edit:
                                if umdb.update_user_details(selected_user_to_edit, edit_name, edit_email, edit_role):
                                    st.rerun()
                    else:
                        st.error("Usuário não encontrado para edição.")


        elif admin_action == "Excluir Usuário":
            st.subheader("Excluir Usuário")
            users_list = [u['username'] for u in umdb.get_all_usernames_and_roles()]
            if not users_list:
                st.info("Nenhum usuário para excluir.")
            else:
                selected_user_to_delete = st.selectbox("Selecione o usuário para excluir", users_list)
                if st.button(f"Confirmar Exclusão de {selected_user_to_delete}", type="primary"):
                    if selected_user_to_delete == st.session_state.username and umdb.get_users_collection().count_documents({"role": "admin"}) <= 1:
                         st.error("Você não pode excluir a si mesmo se for o único administrador.")
                    elif umdb.delete_user(selected_user_to_delete):
                        st.rerun()

        elif admin_action == "Redefinir Senha de Usuário":
            st.subheader("Redefinir Senha de Usuário")
            users_list = [u['username'] for u in umdb.get_all_usernames_and_roles()]
            if not users_list:
                st.info("Nenhum usuário disponível.")
            else:
                selected_user_to_reset_pass = st.selectbox("Selecione o usuário", users_list)
                with st.form("form_reset_senha", clear_on_submit=True):
                    new_plain_password = st.text_input("Nova Senha", type="password")
                    confirm_password = st.text_input("Confirmar Nova Senha", type="password")
                    submit_reset = st.form_submit_button("Redefinir Senha")

                    if submit_reset:
                        if new_plain_password and new_plain_password == confirm_password:
                            if umdb.update_user_password_by_admin(selected_user_to_reset_pass, new_plain_password):
                                st.rerun()
                        elif new_plain_password != confirm_password:
                            st.warning("As senhas não coincidem.")
                        else:
                            st.warning("Por favor, insira a nova senha.")

        st.sidebar.info("Você tem acesso total como administrador.")
        # Aqui o código principal da sua aplicação para administradores continua
        # st.title("Simulador Comercial - Visão Administrador")
        # ... seu código de simulador ... (as páginas em `pages/` já farão o controle)


    # --- Código Comum do Simulador (será renderizado abaixo das opções de admin/user se houver) ---
    # Ou, mais provavelmente, você vai querer que o conteúdo principal seja mostrado
    # nas páginas dentro da pasta `pages/`.
    # Para este arquivo principal, podemos deixar um dashboard ou uma introdução.

    st.markdown("---")
    st.header("Funcionalidades Principais do Simulador")
    st.write("Use o menu na barra lateral para navegar entre as diferentes seções do simulador e opções da sua conta.")
    st.write("As páginas específicas do simulador estão disponíveis no menu de navegação que aparece ao expandir a seção 'Pages' (se houver páginas na pasta `pages`).")

    # Exemplo de como você pode estar estruturando sua app (mantendo seu código original se aplicável)
    # if 'df_simulador' not in st.session_state:
    #     st.session_state.df_simulador = pd.DataFrame() # Inicializa se necessário

    # ... restante do seu código original do Simulador_Comercial.py que deve ser visível para todos os logados ...
    # Por exemplo:
    # st.subheader("Dashboard Principal")
    # st.write("Aqui você pode adicionar um resumo ou dashboard principal do simulador.")

else:
    st.info("Aguardando login...")