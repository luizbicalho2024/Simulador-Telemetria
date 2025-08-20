# pages/Comandos_Rastreadores.py
import streamlit as st
import user_management_db as umdb
from twilio_utils import send_sms # Importa a nossa nova função

# --- 1. CONFIGURAÇÃO E AUTENTICAÇÃO ---
st.set_page_config(
    layout="wide",
    page_title="Comandos Rastreadores",
    page_icon="imgs/v-c.png"
)

if not st.session_state.get("authentication_status"):
    st.error("🔒 Acesso Negado! Por favor, faça login para visualizar esta página.")
    st.stop()

# --- 2. INTERFACE ---
st.sidebar.image("imgs/v-c.png", width=120)
if st.sidebar.button("🧹 Limpar Campos", use_container_width=True, key="cmd_clear"):
    keys_to_clear = [k for k in st.session_state if k.startswith("cmd_")]
    for k in keys_to_clear: del st.session_state[k]
    st.toast("Campos limpos!", icon="✨"); st.rerun()

try:
    st.image("imgs/logo.png", width=250)
except: pass

st.markdown("<h1 style='text-align: center; color: #006494;'>Gerador e Enviador de Comandos Suntech</h1>", unsafe_allow_html=True)
st.markdown("---")

st.sidebar.header("🔧 Configuração Principal")
serial = st.sidebar.text_input("📟 Insira o Serial do Equipamento:", key="cmd_serial")
numero_chip = st.sidebar.text_input("📱 Insira o Nº do Chip (SIM Card):", key="cmd_chip", help="Insira o número com o DDD, ex: 69912345678")

if not serial or len(serial) < 5:
    st.info("Por favor, insira um número de série válido na barra lateral para gerar os comandos.")
    st.stop()

# --- FUNÇÃO PARA EXIBIR COMANDO E BOTÃO ---
def exibir_comando_com_botao(titulo, comando, key_sufixo):
    st.markdown(f"##### {titulo}")
    col1, col2 = st.columns([3, 1])
    with col1:
        st.code(comando, language='text')
    with col2:
        if st.button("📲 Enviar SMS", key=f"btn_{key_sufixo}", use_container_width=True):
            if not numero_chip:
                st.error("Por favor, insira o número do chip na barra lateral.")
            else:
                with st.spinner("A enviar SMS pela Twilio..."):
                    sucesso, status_msg = send_sms(numero_chip, comando)
                if sucesso:
                    st.toast(status_msg, icon="✅")
                else:
                    st.error(status_msg)

# --- 3. ABAS POR MODELO ---
st.success(f"A gerar comandos para o serial: **{serial}**")
tab_st310u, tab_st4305, tab_st390 = st.tabs(["ST310U / ST340", "ST4305", "ST390"])

with tab_st310u:
    st.header("Modelo ST310U / ST340")
    with st.expander("⚙️ Configuração de Rede (IP, Porta e APN)", expanded=True):
        apn = st.text_input("APN:", value="allcom.claro.com.br", key="cmd_310_apn")
        user = st.text_input("Utilizador APN:", value="allcom", key="cmd_310_user")
        pwd = st.text_input("Senha APN:", value="allcom", key="cmd_310_pwd", type="password")
        ip1 = st.text_input("IP Primário:", value="54.94.190.167", key="cmd_310_ip1")
        porta1 = st.text_input("Porta Primária:", value="9601", key="cmd_310_porta1")
        comando_ntw = f"ST300NTW;{serial};02;1;{apn};{user};{pwd};{ip1};{porta1};;;"
        exibir_comando_com_botao("Comando de Rede", comando_ntw, "ntw_310")

    with st.expander("▶️ Ações Remotas"):
        exibir_comando_com_botao("Solicitar Posição Atual", f"ST300POS;{serial};02", "pos_310")
        exibir_comando_com_botao("Reiniciar o Equipamento (Reboot)", f"ST300RST;{serial};02", "rst_310")
        exibir_comando_com_botao("Ativar Saída 1 (Bloqueio)", f"ST300OUT;{serial};02;1;1", "out1_on_310")
        exibir_comando_com_botao("Desativar Saída 1 (Desbloqueio)", f"ST300OUT;{serial};02;1;0", "out1_off_310")

with tab_st4305:
    st.header("Modelo ST4305")
    with st.expander("⚙️ Configuração de Rede (APN, IP e Porta)", expanded=True):
        apn_4305 = st.text_input("APN:", value="allcomiot.vivo.com.br", key="cmd_4305_apn")
        user_4305 = st.text_input("Utilizador APN:", value="allcom", key="cmd_4305_user")
        pwd_4305 = st.text_input("Senha APN:", value="allcom", key="cmd_4305_pwd", type="password")
        comando_apn = f'PRG;{serial};10;00#01;01#{apn_4305};02#{user_4305};03#{pwd_4305}'
        comando_ip = f'PRG;{serial};10;05#54.94.190.167;06#9601;08#54.94.190.167;09#9601'
        exibir_comando_com_botao("APN", comando_apn, "apn_4305")
        exibir_comando_com_botao("IP e Porta", comando_ip, "ip_4305")
    
    with st.expander("▶️ Ações Remotas"):
        exibir_comando_com_botao("Reboot (Reiniciar)", f'CMD;{serial};03;03', "reboot_4305")
        exibir_comando_com_botao("Solicitar Posição", f'CMD;{serial};03;01', "pos_4305")

with tab_st390:
    st.header("Modelo ST390")
    with st.expander("⚙️ Configuração de Rede (APN, IP e Porta)", expanded=True):
        apn_390 = st.text_input("APN:", value="allcom.claro.com.br", key="cmd_390_apn")
        comando_apn_390 = f'ST400CMD;{serial};;{apn_390};1'
        comando_ip_390 = f'ST400CMD;{serial};;54.94.190.167;9601;54.94.190.167;9601'
        exibir_comando_com_botao("APN", comando_apn_390, "apn_390")
        exibir_comando_com_botao("IP e Porta", comando_ip_390, "ip_390")

    with st.expander("▶️ Ações Remotas"):
        # (Adicione aqui outros comandos de ação para o ST390, se necessário)
        pass
