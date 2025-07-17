# pages/Comandos_Rastreadores.py
import streamlit as st
import user_management_db as umdb

# --- 1. CONFIGURAÇÃO E AUTENTICAÇÃO ---
st.set_page_config(
    layout="wide",
    page_title="Comandos Suntech",
    page_icon="imgs/v-c.png"
)

if not st.session_state.get("authentication_status"):
    st.error("🔒 Acesso Negado! Por favor, faça login."); st.stop()

# --- 2. INTERFACE ---
st.sidebar.image("imgs/v-c.png", width=120)
if st.sidebar.button("🧹 Limpar Campos", use_container_width=True, key="cmd_clear"):
    keys_to_clear = [k for k in st.session_state if k.startswith("cmd_")]
    for k in keys_to_clear: del st.session_state[k]
    st.toast("Campos limpos!", icon="✨"); st.rerun()

try:
    st.image("imgs/logo.png", width=250)
except: pass

st.markdown("<h1 style='text-align: center; color: #54A033;'>Simulador de Comandos Suntech e-Trac</h1>", unsafe_allow_html=True)
st.markdown("---")
st.write(f"Usuário: {st.session_state.get('name', 'N/A')} ({st.session_state.get('username', 'N/A')})")
st.write(f"Nível de Acesso: {st.session_state.get('role', 'Indefinido').capitalize()}")
st.markdown("---")

st.sidebar.header("🔧 Configuração do Simulador")
serial = st.sidebar.text_input("📟 Insira o Serial:", value="XXXXXXX", key="cmd_serial")

left_column, right_column = st.columns(2)

with left_column:
    st.subheader("📡 Selecione o Modelo")
    mod_rastreador = st.radio('Modelos disponíveis:', ("ST310U", "ST4315", "ST300HD"), key="cmd_modelo")

# --- 3. LÓGICA DE GERAÇÃO DE COMANDOS ---
if not serial or serial == "XXXXXXX":
    st.warning("⚠️ Insira um serial válido para gerar os comandos.")
else:
    # Registra o log apenas uma vez quando o serial é válido
    if "log_generated" not in st.session_state or st.session_state.log_generated != serial:
        umdb.add_log(st.session_state["username"], "Gerou Comandos", f"Modelo: {mod_rastreador}, Serial: {serial}")
        st.session_state.log_generated = serial

    with right_column:
        if mod_rastreador == 'ST310U':
            st.subheader("📜 Comandos para ST310U")
            apn = st.text_input("Digite a APN:", value="allcom.claro.com.br", key="cmd_apn_310")
            user = st.text_input("Digite o Usuário:", value="allcom", key="cmd_user_310")
            password = st.text_input("Digite a Senha:", value="allcom", key="cmd_pass_310", type="password")
            
            st.text("IP, PORT e APN e-Trac"); st.code(f"ST300NTW;{serial};02;1;{apn};{user};{password};54.94.190.167;9601;35.198.41.183;9601;;")
            st.text("Disable ZIP"); st.code(f'ST300SVC;{serial};02;1;180;0;0;0;1;1;0;1;0;0;1;0')
            # ... (outros comandos)

        elif mod_rastreador == 'ST4315':
            st.subheader("📜 Comandos para ST4315")
            apn_4315 = st.text_input("Digite a APN:", value="allcomiot.vivo.com.br", key="cmd_apn_4315")
            # ... (outros inputs e comandos)

        elif mod_rastreador == 'ST300HD':
            st.subheader("📜 Comandos para ST300HD")
            idM_st300hd = st.text_input("Digite o Número do Motorista:", key="cmd_idm_300")
            ibutton_st300hd = st.text_input("Digite o Serial do Ibutton:", key="cmd_ibutton_300")
            st.text("Adicionar motorista"); st.code(f'ST300HAD;{serial};02;{idM_st300hd};{ibutton_st300hd}')
            st.text("Remover motorista"); st.code(f'ST300HRD;{serial};02;{idM_st300hd}')
