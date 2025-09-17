# pages/Comandos_Rastreadores.py
import streamlit as st
import user_management_db as umdb
from twilio_utils import send_sms

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
serial = st.sidebar.text_input("📟 Insira o Serial (Modelos Antigos):", key="cmd_serial")
esn_4315 = st.sidebar.text_input("📟 Insira o ESN (ST4315U - 10 dígitos):", key="cmd_4315_esn", max_chars=10)
numero_chip = st.sidebar.text_input("📱 Insira o Nº do Chip (SIM Card):", key="cmd_chip", help="Insira o número com o DDD, ex: 69912345678")

# --- FUNÇÃO PARA EXIBIR COMANDO E BOTÃO ---
def exibir_comando_com_botao(titulo, comando, key_sufixo, target_id):
    st.markdown(f"**{titulo}**")
    col1, col2 = st.columns([3, 1])
    with col1:
        st.code(comando, language='text')
    with col2:
        if st.button("📲 Enviar SMS", key=f"btn_{key_sufixo}", use_container_width=True):
            if not numero_chip:
                st.error("Por favor, insira o número do chip na barra lateral.")
            elif not target_id:
                st.error("Por favor, insira o Serial ou ESN do equipamento.")
            else:
                with st.spinner("A enviar SMS pela Twilio..."):
                    sucesso, status_msg = send_sms(numero_chip, comando)
                if sucesso:
                    st.toast(status_msg, icon="✅")
                    umdb.add_log(st.session_state["username"], "Enviou Comando SMS", {"id_equipamento": target_id, "comando": titulo})
                else:
                    st.error(status_msg)

# --- 3. ABAS POR MODELO ---
tab_st310u, tab_st4305, tab_st390, tab_st4315u = st.tabs(["ST310U / ST340", "ST4305", "ST390", "ST4315U"])

# --- ABA ST310U / ST340 ---
with tab_st310u:
    if not serial:
        st.info("Por favor, insira um número de série na barra lateral para gerar os comandos para este modelo.")
    else:
        st.header("Modelo ST310U / ST340")
        with st.expander("⚙️ Configuração de Rede (IP, Porta e APN)", expanded=True):
            apn = st.text_input("APN:", value="allcom.claro.com.br", key="cmd_310_apn")
            user = st.text_input("Utilizador APN:", value="allcom", key="cmd_310_user")
            pwd = st.text_input("Senha APN:", value="allcom", key="cmd_310_pwd", type="password")
            ip1 = st.text_input("IP Primário:", value="54.94.190.167", key="cmd_310_ip1")
            porta1 = st.text_input("Porta Primária:", value="9601", key="cmd_310_porta1")
            comando_ntw = f"ST300NTW;{serial};02;1;{apn};{user};{pwd};{ip1};{porta1};;;"
            exibir_comando_com_botao("Comando de Rede", comando_ntw, "ntw_310", serial)
        with st.expander("▶️ Ações Remotas"):
            exibir_comando_com_botao("Solicitar Posição Atual", f"ST300POS;{serial};02", "pos_310", serial)
            exibir_comando_com_botao("Reiniciar o Equipamento (Reboot)", f"ST300RST;{serial};02", "rst_310", serial)
            exibir_comando_com_botao("Ativar Saída 1 (Bloqueio)", f"ST300OUT;{serial};02;1;1", "out1_on_310", serial)
            exibir_comando_com_botao("Desativar Saída 1 (Desbloqueio)", f"ST300OUT;{serial};02;1;0", "out1_off_310", serial)

# --- ABA ST4305 ---
with tab_st4305:
    if not serial:
        st.info("Por favor, insira um número de série na barra lateral para gerar os comandos para este modelo.")
    else:
        st.header("Modelo ST4305")
        with st.expander("⚙️ Configuração de Rede (APN, IP e Porta)", expanded=True):
            apn_4305 = st.text_input("APN:", value="allcomiot.vivo.com.br", key="cmd_4305_apn")
            user_4305 = st.text_input("Utilizador APN:", value="allcom", key="cmd_4305_user")
            pwd_4305 = st.text_input("Senha APN:", value="allcom", key="cmd_4305_pwd", type="password")
            comando_apn = f'PRG;{serial};10;00#01;01#{apn_4305};02#{user_4305};03#{pwd_4305}'
            comando_ip = f'PRG;{serial};10;05#54.94.190.167;06#9601;08#54.94.190.167;09#9601'
            exibir_comando_com_botao("APN", comando_apn, "apn_4305", serial)
            exibir_comando_com_botao("IP e Porta", comando_ip, "ip_4305", serial)
        with st.expander("▶️ Ações Remotas"):
            exibir_comando_com_botao("Reboot (Reiniciar)", f'CMD;{serial};03;03', "reboot_4305", serial)
            exibir_comando_com_botao("Solicitar Posição", f'CMD;{serial};03;01', "pos_4305", serial)

# --- ABA ST390 ---
with tab_st390:
    if not serial:
        st.info("Por favor, insira um número de série na barra lateral para gerar os comandos para este modelo.")
    else:
        st.header("Modelo ST390")
        with st.expander("⚙️ Configuração de Rede (APN, IP e Porta)", expanded=True):
            apn_390 = st.text_input("APN:", value="allcom.claro.com.br", key="cmd_390_apn")
            comando_apn_390 = f'ST400CMD;{serial};;{apn_390};1'
            comando_ip_390 = f'ST400CMD;{serial};;54.94.190.167;9601;54.94.190.167;9601'
            exibir_comando_com_botao("APN", comando_apn_390, "apn_390", serial)
            exibir_comando_com_botao("IP e Porta", comando_ip_390, "ip_390", serial)

# --- NOVA ABA ST4315U ---
with tab_st4315u:
    if not esn_4315 or not esn_4315.isdigit() or len(esn_4315) != 10:
        st.info("Por favor, insira um ESN válido de 10 dígitos na barra lateral para gerar os comandos para este modelo.")
    else:
        st.header("Modelo ST4315U")
        with st.expander("⚙️ Configuração de Rede (APN, IP e Porta)", expanded=True):
            auth_options = {"CHAP (Recomendado Getrak)": "01", "PAP": "00", "Automático": "02", "Nenhum": "03"}
            band_options = {
                "LTE Cat. M1 (4G) e GSM (2G) (Recomendado)": "01", "LTE Cat. M1 (4G) somente": "00",
                "LTE Cat. NB somente": "02", "LTE Cat. M1 e Cat. NB": "03", "LTE Cat. M1, Cat. NB e GSM": "04",
                "GSM (2G) somente": "05"
            }
            col_apn1, col_apn2 = st.columns(2)
            auth_sel = col_apn1.selectbox("Autenticação:", list(auth_options.keys()), key="cmd_4315_auth")
            apn = st.text_input("APN:", value="conexao.getrak.com", key="cmd_4315_apn")
            user = st.text_input("Utilizador APN:", key="cmd_4315_user")
            pwd = st.text_input("Senha APN:", key="cmd_4315_pwd", type="password")
            cmd_apn = f"PRG;{esn_4315};10;00#{auth_options[auth_sel]};01#{apn};02#{user};03#{pwd}"
            exibir_comando_com_botao("Configuração de APN", cmd_apn, "apn_4315", esn_4315)

            ip1 = st.text_input("IP Primário:", "st4315.getrak.com.br", key="cmd_4315_ip1")
            porta1 = st.text_input("Porta Primária:", "13018", key="cmd_4315_porta1")
            cmd_ip = f"PRG;{esn_4315};10;05#{ip1};06#{porta1};08#{ip1};09#{porta1}"
            exibir_comando_com_botao("Configuração de DNS/IP, Porta", cmd_ip, "ip_4315", esn_4315)
            
            exibir_comando_com_botao("Configuração de Protocolo de Rede (TCP)", f"PRG;{esn_4315};10;07#00;10#00", "tcp_4315", esn_4315)
            exibir_comando_com_botao("Desabilitar Parâmetro ZIP", f"PRG;{esn_4315};10;55#00", "zip_4315", esn_4315)

        with st.expander("⏱️ Configuração de Tempos de Comunicação"):
            exibir_comando_com_botao("Tempos Padrão (1h desligado, 2min ligado)", f"PRG;{esn_4315};16;70#3600;71#0;72#0;73#120;74#0;75#0;76#0;77#0;78#0;79#120;80#0;81#30;82#120;83#0;84#30;85#120;86#0;87#30", "tempos_full_4315", esn_4315)
            exibir_comando_com_botao("Tempos Simplificados (Ignição ligada/desligada)", f"PRG;{esn_4315};16;70#3600;79#120", "tempos_simple_4315", esn_4315)
            vel = st.number_input("Velocidade para Alerta (km/h):", 0, value=110, step=5, key="cmd_4315_vel")
            if vel > 0:
                exibir_comando_com_botao("Configurar Excesso de Velocidade", f"PRG;{esn_4315};16;21#{vel}", "vel_4315", esn_4315)

        with st.expander("🔑 Configuração de Ignição"):
            exibir_comando_com_botao("Ignição Física (Pós Chave)", f"PRG;{esn_4315};17;00#01", "ign_fisica_4315", esn_4315)
            exibir_comando_com_botao("Ignição Virtual por Acelerômetro", f"PRG;{esn_4315};17;00#03", "ign_acel_4315", esn_4315)
            exibir_comando_com_botao("Ignição Virtual por Tensão", f"PRG;{esn_4315};17;00#02", "ign_tensao_4315", esn_4315)
            col_t1, col_t2 = st.columns(2)
            t_alta = col_t1.number_input("Tensão para Ligar (Ex: 13.2V -> 132)", value=132, key="cmd_4315_t_alta")
            t_baixa = col_t2.number_input("Tensão para Desligar (Ex: 12.8V -> 128)", value=128, key="cmd_4315_t_baixa")
            cmd_ign_tensao = f"PRG;{esn_4315};17;15#{t_alta};16#{t_baixa}"
            exibir_comando_com_botao("Ajustar Tensão de Ignição Virtual", cmd_ign_tensao, "ign_tensao_ajuste_4315", esn_4315)

        with st.expander("▶️ Ações Remotas"):
            exibir_comando_com_botao("Reiniciar Equipamento", f"CMD;{esn_4315};03;03", "reboot_4315", esn_4315)
            exibir_comando_com_botao("Solicitar Posição", f"CMD;{esn_4315};03;01", "pos_4315", esn_4315)
            exibir_comando_com_botao("Ativar Saída 1", f"CMD;{esn_4315};04;01", "out1_on_4315", esn_4315)
            exibir_comando_com_botao("Desativar Saída 1", f"CMD;{esn_4315};04;02", "out1_off_4315", esn_4315)

        with st.expander("⚙️ Configurações Avançadas"):
            exibir_comando_com_botao("Configurar String de Dados", f"PRG;{esn_4315};10;80#00fff83f;82#00fff83f;84#00fff83f;86#00;87#00001ffbff;97#00", "string_dados_4315", esn_4315)
            exibir_comando_com_botao("Configuração Global 1", f"PRG;{esn_4315};10;81#0007800f", "global1_4315", esn_4315)
            exibir_comando_com_botao("Configuração Global 2", f"PRG;{esn_4315};11;00#02;01#01;02#00;03#50;04#00;05#00;06#00;07#00;08#00;09#00;10#00;11#00;12#00;13#00;14#00;40#01;41#02;42#06;43#00;44#00", "global2_4315", esn_4315)
            exibir_comando_com_botao("Configuração Global 3", f"PRG;{esn_4315};11;45#00;46#00;47#00;60#00;61#00;62#00;63#00;64#00;65#00;66#00;67#00", "global3_4315", esn_4315)
            hodometro = st.number_input("Ajustar Hodômetro (metros):", 0, 1000000000, step=1000, key="cmd_4315_hodometro")
            if hodometro > 0:
                exibir_comando_com_botao("Ajustar Hodômetro", f"CMD;{esn_4315};05;03;{hodometro}", "hodometro_4315", esn_4315)

        with st.expander("🏍️ Configurações para Motos"):
            exibir_comando_com_botao("Config. Moto 1", f"PRG;{esn_4315};10;60#0;70#00", "moto1_4315", esn_4315)
            exibir_comando_com_botao("Config. Moto 2", f"PRG;{esn_4315};19;00#02;01#0.10", "moto2_4315", esn_4315)
            exibir_comando_com_botao("Config. Moto 3", f"PRG;{esn_4315};19;01", "moto3_4315", esn_4315)
            exibir_comando_com_botao("Config. Moto 4", f"PRG;{esn_4315};17;01#120", "moto4_4315", esn_4315)
            exibir_comando_com_botao("Config. Moto 5", f"PRG;{esn_4315};16;70#0", "moto5_4315", esn_4315)
