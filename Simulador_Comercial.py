# Simulador_Comercial.py
import streamlit as st
import pandas as pd
import user_management_db as umdb
import streamlit_authenticator as stauth

# --- 1. CONFIGURAÇÃO INICIAL DA PÁGINA (COM LOGO E FAVICON) ---
st.set_page_config(
    page_title="Simulador Telemetria",
    layout="wide",
    page_icon="imgs/v-c.png"  # Caminho para o seu favicon
)

# --- Exibe o logo no topo da página ---
try:
    st.image("imgs/logo.png", width=250)  # Caminho para a sua imagem de logo
except Exception as e:
    # Este erro não impede a execução, apenas avisa nos logs se o logo não for encontrado
    print(f"WARN: Logo não encontrado em 'imgs/logo.png': {e}")


# --- 2. VERIFICAÇÃO DA CONEXÃO COM A BASE DE DADOS ---
if not umdb.get_mongo_client():
    st.error("🚨 FALHA CRÍTICA NA CONEXÃO COM A BASE DE DADOS.")
    st.info("""
        **Possíveis Causas e Soluções:**
        1.  **Segredos (Secrets) Incorretos:** Verifique se a `MONGO_CONNECTION_STRING` nos segredos da sua aplicação no Streamlit Cloud está correta.
        2.  **IP Não Autorizado:** No seu MongoDB Atlas, vá a "Network Access" e certifique-se de que o acesso de qualquer IP está autorizado (`0.0.0.0/0`).
    """)
    st.stop()

# --- 3. CONFIGURAÇÃO DO AUTENTICADOR ---
credentials = umdb.fetch_all_users_for_auth()
authenticator = stauth.Authenticate(
    credentials,
    st.secrets["AUTH_COOKIE_NAME"],
    st.secrets["AUTH_COOKIE_KEY"],
    cookie_expiry_days=st.secrets.get("AUTH_COOKIE_EXPIRY_DAYS", 30),
    preauthorized=None
)

# --- 4. LÓGICA PRINCIPAL DA APLICAÇÃO ---

# A. Caso não haja utilizadores -> Criar o primeiro admin
if not credentials.get("usernames"):
    st.title("🚀 Bem-vindo ao Simulador de Telemetria!")
    st.subheader("Configuração Inicial: Crie a sua Conta de Administrador")
    with st.form("form_criar_primeiro_admin"):
        admin_name = st.text_input("Nome Completo")
        admin_username = st.text_input("Nome de Utilizador (para login)")
        admin_email = st.text_input("Email")
        admin_password = st.text_input("Senha", type="password")
        if st.form_submit_button("✨ Criar Administrador"):
            if all([admin_name, admin_username, admin_email, admin_password]):
                if umdb.add_user(admin_username, admin_name, admin_email, admin_password, "admin"):
                    st.success("Conta de administrador criada com sucesso! A página será recarregada.")
                    st.rerun()
            else:
                st.warning("Por favor, preencha todos os campos.")
    st.stop()


# B. Processo de Login
# A função login desenha os campos na tela.
authenticator.login(location='main')

if st.session_state["authentication_status"]:
    # --- LOGIN BEM-SUCEDIDO ---
    name = st.session_state["name"]
    username = st.session_state["username"]
    st.session_state.role = umdb.get_user_role(username)

    st.sidebar.title(f"Olá, {name}! 👋")
    authenticator.logout("Sair", "sidebar")

    # C. Painel do Utilizador Comum
    if st.session_state.role == "user":
        st.sidebar.subheader("Minha Conta")
        with st.sidebar.expander("Alterar a Minha Senha"):
            with st.form("form_alterar_senha_user", clear_on_submit=True):
                current_pwd = st.text_input("Senha Atual", type="password")
                new_pwd = st.text_input("Nova Senha", type="password")
                if st.form_submit_button("Salvar Nova Senha"):
                    user_hash = credentials["usernames"][username]["password"]
                    if umdb.verify_password(current_pwd, user_hash):
                        if umdb.update_user_password(username, new_pwd):
                            st.success("Senha alterada com sucesso!")
                        else:
                            st.error("Ocorreu um erro ao alterar a senha.")
                    else:
                        st.error("A sua senha atual está incorreta.")

    # D. Painel de Administração
    elif st.session_state.role == "admin":
        st.sidebar.subheader("Painel de Admin")
        
        tab_ver, tab_cad, tab_edit, tab_del = st.tabs(["👁️ Ver Utilizadores", "➕ Cadastrar", "✏️ Editar", "🗑️ Excluir"])

        with tab_ver:
            st.dataframe(umdb.get_all_users_for_admin_display(), use_container_width=True, hide_index=True)

        with tab_cad:
            with st.form("form_cadastrar", clear_on_submit=True):
                st.subheader("Cadastrar Novo Utilizador")
                uname = st.text_input("Nome de Utilizador")
                nome = st.text_input("Nome Completo")
                mail = st.text_input("Email")
                pwd = st.text_input("Senha", type="password")
                role = st.selectbox("Papel", ["user", "admin"], format_func=str.capitalize)
                if st.form_submit_button("Cadastrar Utilizador"):
                    if umdb.add_user(uname, nome, mail, pwd, role):
                        st.success(f"Utilizador '{uname}' criado.")
                        st.rerun()

        users_dict = {u['username']: u for u in umdb.get_all_users_for_admin_display()}
        if users_dict:
            user_to_manage = st.selectbox("Selecione um utilizador para gerir:", list(users_dict.keys()), key="user_select_manage")

            with tab_edit:
                with st.form(f"form_edit_{user_to_manage}"):
                    st.subheader(f"A editar: {user_to_manage}")
                    user_data = users_dict.get(user_to_manage, {})
                    new_name = st.text_input("Nome Completo", value=user_data.get('name', ''))
                    new_email = st.text_input("Email", value=user_data.get('email', ''))
                    role_idx = ["user", "admin"].index(user_data.get('role', 'user'))
                    new_role = st.selectbox("Papel", ["user", "admin"], index=role_idx, format_func=str.capitalize)
                    if st.form_submit_button("Salvar Alterações"):
                        if umdb.update_user_details(user_to_manage, new_name, new_email, new_role):
                            st.success("Detalhes atualizados.")
                            st.rerun()

            with tab_del:
                st.subheader(f"Excluir: {user_to_manage}")
                st.warning(f"⚠️ Atenção: esta ação é irreversível.")
                if st.button(f"Excluir Permanentemente '{user_to_manage}'", type="primary"):
                    if umdb.delete_user(user_to_manage):
                        st.success(f"Utilizador '{user_to_manage}' excluído.")
                        st.rerun()
        else:
             st.info("Nenhum utilizador para gerir.")

    # E. Conteúdo Principal da Página (visível para todos os logados)
    st.markdown("---")
    st.header("Análises e Simuladores")
    st.write("Navegue pelas ferramentas disponíveis no menu lateral esquerdo.")
    st.success("Login realizado com sucesso. Bem-vindo(a) à plataforma!")


elif st.session_state["authentication_status"] is False:
    st.error('❌ Nome de utilizador ou senha incorreto(s).')
elif st.session_state["authentication_status"] is None:
    st.title("Simulador de Telemetria")
    st.info('👋 Por favor, insira o seu nome de utilizador e senha para aceder.')
