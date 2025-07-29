# pages/Comandos_Rastreadores.py
import streamlit as st
import user_management_db as umdb

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

st.markdown("<h1 style='text-align: center; color: #006494;'>Gerador de Comandos Suntech</h1>", unsafe_allow_html=True)
st.markdown("---")
st.write(f"Usuário: {st.session_state.get('name', 'N/A')} ({st.session_state.get('username', 'N/A')})")
st.write(f"Nível de Acesso: {st.session_state.get('role', 'Indefinido').capitalize()}")
st.markdown("---")

st.sidebar.header("🔧 Configuração Principal")
serial = st.sidebar.text_input("📟 Insira o Serial do Equipamento:", key="cmd_serial")

if not serial or len(serial) < 5:
    st.info("Por favor, insira um número de série válido na barra lateral para gerar os comandos.")
    st.stop()

st.success(f"A gerar comandos para o serial: **{serial}**")

# --- 3. ABAS POR MODELO ---
tab_st310u, tab_st300hd, tab_st4305, tab_st390 = st.tabs(["ST310U / ST340", "ST300HD", "ST4305", "ST390"])

with tab_st310u:
    st.header("Modelo ST310U / ST340")
    with st.expander("Configuração de Rede (IP, Porta e APN)", expanded=True):
        apn = st.text_input("APN:", value="allcom.claro.com.br", key="cmd_310_apn")
        user = st.text_input("Utilizador APN:", value="allcom", key="cmd_310_user")
        pwd = st.text_input("Senha APN:", value="allcom", key="cmd_310_pwd", type="password")
        ip1 = st.text_input("IP Primário:", value="54.94.190.167", key="cmd_310_ip1")
        porta1 = st.text_input("Porta Primária:", value="9601", key="cmd_310_porta1")
        st.code(f"ST300NTW;{serial};02;1;{apn};{user};{pwd};{ip1};{porta1};;;")

    with st.expander("Intervalos de Comunicação"):
        st.markdown("##### Intervalo Padrão (Carro)")
        st.code(f'ST300RPT;{serial};02;3600;120;3600;1;0;600;0;0;0')
        st.markdown("##### Intervalo para Motos (Otimizado)")
        st.code(f'ST300RPT;{serial};02;0;60;0;1;0;0;0;0;0')

    with st.expander("Outras Configurações Essenciais"):
        st.markdown("##### Habilitar/Desabilitar Transmissão de Dados")
        st.code(f"ST300SVC;{serial};02;1;180;0;0;0;1;1;0;1;0;0;1;0")
        st.markdown("##### Protocolo TCP/IP")
        st.code(f"ST300ADP;{serial};02;T;T;1;;0;0;0;0;0;0")
        st.markdown("##### Configuração de Eventos")
        st.code(f"ST300EVT;{serial};02;0;10;0;12;3;9;30;20;0;1;7;1;1;0;0;0;0;0;0;9;9;0;0;0")
        st.markdown("##### Parâmetros de Ângulo (NPTs)")
        st.code(f"ST300NPT;{serial};02;20.0;1;30;0;1;500;300;5;10;100;10;180;100;1")

with tab_st300hd:
    st.header("Modelo ST300HD (Identificador de Motorista)")
    with st.expander("Gestão de Motoristas (iButton)", expanded=True):
        id_motorista = st.text_input("ID do Motorista (ex: 101):", key="cmd_300_id")
        serial_ibutton = st.text_input("Serial do iButton (16 dígitos hex):", key="cmd_300_ibutton")
        if id_motorista and serial_ibutton:
            st.markdown("##### Adicionar Motorista")
            st.code(f'ST300HAD;{serial};02;{id_motorista};{serial_ibutton}')
            st.markdown("##### Remover Motorista")
            st.code(f'ST300HRD;{serial};02;{id_motorista}')

with tab_st4305:
    st.header("Modelo ST4305")
    with st.expander("Configuração de Rede (APN, IP e Porta)", expanded=True):
        apn_4305 = st.text_input("APN:", value="allcomiot.vivo.com.br", key="cmd_4305_apn")
        user_4305 = st.text_input("Utilizador APN:", value="allcom", key="cmd_4305_user")
        pwd_4305 = st.text_input("Senha APN:", value="allcom", key="cmd_4305_pwd", type="password")
        st.markdown("##### APN")
        st.code(f'PRG;{serial};10;00#01;01#{apn_4305};02#{user_4305};03#{pwd_4305}')
        st.markdown("##### IP e Porta")
        st.code(f'PRG;{serial};10;05#54.94.190.167;06#9601;08#54.94.190.167;09#9601')

    with st.expander("Intervalos e Ângulo"):
        igon_4305 = st.number_input("Intervalo Ligado (Segundos):", value=120, key="cmd_4305_igon")
        igoff_4305 = st.number_input("Intervalo Desligado (Segundos):", value=3600, key="cmd_4305_igoff")
        ang_4305 = st.number_input("Ângulo (Graus):", value=45, key="cmd_4305_ang")
        st.code(f'PRG;{serial};16;70#{igoff_4305};71#0;72#0;73#{igon_4305};74#0;75#0;76#0;77#0;78#0;79#120;80#0;81#{ang_4305};82#120;83#0;84#{ang_4305};85#120;86#0;87#{ang_4305}')

    with st.expander("Comandos Diversos"):
        st.markdown("##### Protocolo TCP e ZIP Desabilitado")
        st.code(f'PRG;{serial};10;07#00;10#00;55#00')
        st.markdown("##### Ignição Física")
        st.code(f'PRG;{serial};17;00#01')
        st.markdown("##### Ignição Virtual (Acelerômetro)")
        st.code(f'PRG;{serial};17;00#03')
        st.markdown("##### Reboot (Reiniciar)")
        st.code(f'CMD;{serial};03;03')
        st.markdown("##### Solicitar Posição")
        st.code(f'CMD;{serial};03;01')

with tab_st390:
    st.header("Modelo ST390")
    with st.expander("Configuração de Rede (APN, IP e Porta)", expanded=True):
        apn_390 = st.text_input("APN:", value="allcom.claro.com.br", key="cmd_390_apn")
        st.markdown("##### APN")
        st.code(f'ST400CMD;{serial};;{apn_390};1')
        st.markdown("##### IP e Porta")
        st.code(f'ST400CMD;{serial};;54.94.190.167;9601;54.94.190.167;9601')
    
    with st.expander("Intervalos de Comunicação"):
        st.markdown("##### Ignição Ligada")
        st.code(f"ST400SET;{serial};;10;60")
        st.markdown("##### Ignição Desligada")
        st.code(f"ST400SET;{serial};;11;600")
        st.markdown("##### Em Roaming")
        st.code(f"ST400SET;{serial};;12;600")
    
    with st.expander("Comandos Diversos"):
        st.markdown("##### Habilitar Roaming")
        st.code(f"ST400SET;{serial};;30;1")
        st.markdown("##### Ignição Física")
        st.code(f"ST400SET;{serial};;3;1")
        st.markdown("##### Habilitar Hodômetro")
        st.code(f"ST400SET;{serial};;2;1")
