from __future__ import annotations

import streamlit as st

import user_management_db as db
from app_core.auth import require_auth
from app_core.ui import apply_branding, configure_page, render_hero, render_sidebar
from twilio_utils import send_sms

configure_page("Comandos de Rastreadores")
apply_branding()
require_auth()
render_sidebar()
render_hero("Comandos de rastreadores Suntech", "Gere comandos por modelo e, quando a Twilio estiver configurada, envie-os por SMS.")

input_1, input_2, input_3 = st.columns(3)
serial = input_1.text_input("Serial — ST300/ST390", key="cmd_serial")
esn_4315 = input_2.text_input("ESN — ST4315U", max_chars=10, key="cmd_4315_esn")
phone_number = input_3.text_input("Número do chip", placeholder="69912345678", key="cmd_phone")


def show_command(title: str, command: str, key_suffix: str, equipment_id: str) -> None:
    st.markdown(f"**{title}**")
    command_col, action_col = st.columns([4, 1])
    command_col.code(command, language="text")
    if action_col.button("Enviar por SMS", key=f"send_{key_suffix}", width="stretch"):
        if not phone_number.strip():
            st.warning("Informe o número do chip.")
        elif not equipment_id.strip():
            st.warning("Informe o identificador do equipamento.")
        else:
            success, message = send_sms(phone_number, command)
            if success:
                db.add_log(
                    st.session_state.get("username", "sistema"),
                    "Enviou comando por SMS",
                    {"equipamento": equipment_id, "comando": title, "telefone_final": phone_number[-4:]},
                )
                st.success(message)
            else:
                st.error(message)


tab_st300, tab_st390, tab_st4315 = st.tabs(["ST300", "ST390", "ST4315U"])

with tab_st300:
    if not serial.strip():
        st.info("Informe o serial para gerar os comandos do ST300.")
    else:
        with st.expander("Configuração de rede", expanded=True):
            col_1, col_2, col_3 = st.columns(3)
            apn = col_1.text_input("APN", value="allcom.claro.com.br", key="cmd_st300_apn")
            apn_user = col_2.text_input("Usuário APN", value="allcom", key="cmd_st300_user")
            apn_password = col_3.text_input("Senha APN", value="allcom", type="password", key="cmd_st300_password")
            col_4, col_5 = st.columns(2)
            primary_ip = col_4.text_input("IP primário", value="54.94.190.167", key="cmd_st300_ip")
            primary_port = col_5.text_input("Porta primária", value="9601", key="cmd_st300_port")
            show_command(
                "Configurar rede",
                f"ST300NTW;{serial};02;1;{apn};{apn_user};{apn_password};{primary_ip};{primary_port};;;",
                "st300_network",
                serial,
            )

        with st.expander("Ações remotas"):
            show_command("Solicitar posição atual", f"ST300CMD;{serial};02;StatusReq", "st300_position", serial)
            show_command("Reiniciar equipamento", f"ST300RST;{serial};02;Reboot", "st300_reboot", serial)
            show_command("Ativar saída 1 — bloqueio", f"ST300OUT;{serial};02;Enable1", "st300_output_on", serial)
            show_command("Desativar saída 1 — desbloqueio", f"ST300OUT;{serial};02;Disable1", "st300_output_off", serial)

with tab_st390:
    if not serial.strip():
        st.info("Informe o serial para gerar os comandos do ST390.")
    else:
        with st.expander("Configuração de rede", expanded=True):
            apn_390 = st.text_input("APN", value="allcom.claro.com.br", key="cmd_st390_apn")
            ip_390 = st.text_input("IP", value="54.94.190.167", key="cmd_st390_ip")
            port_390 = st.text_input("Porta", value="9601", key="cmd_st390_port")
            show_command("Configurar APN", f"ST400CMD;{serial};;{apn_390};1", "st390_apn", serial)
            show_command("Configurar IP e porta", f"ST400CMD;{serial};;{ip_390};{port_390};{ip_390};{port_390}", "st390_ip", serial)

with tab_st4315:
    valid_esn = esn_4315.isdigit() and len(esn_4315) == 10
    if not valid_esn:
        st.info("Informe um ESN numérico de 10 dígitos para gerar os comandos do ST4315U.")
    else:
        with st.expander("Configuração de rede", expanded=True):
            authentication_options = {
                "CHAP": "01",
                "PAP": "00",
                "Automático": "02",
                "Sem autenticação": "03",
            }
            authentication = st.selectbox("Autenticação", list(authentication_options), key="cmd_4315_auth")
            col_1, col_2, col_3 = st.columns(3)
            apn = col_1.text_input("APN", value="conexao.getrak.com", key="cmd_4315_apn")
            apn_user = col_2.text_input("Usuário APN", key="cmd_4315_user")
            apn_password = col_3.text_input("Senha APN", type="password", key="cmd_4315_password")
            show_command(
                "Configurar APN",
                f"PRG;{esn_4315};10;00#{authentication_options[authentication]};01#{apn};02#{apn_user};03#{apn_password}",
                "4315_apn",
                esn_4315,
            )

            col_4, col_5 = st.columns(2)
            host = col_4.text_input("Host/IP primário", value="st4315.getrak.com.br", key="cmd_4315_host")
            port = col_5.text_input("Porta primária", value="13018", key="cmd_4315_port")
            show_command(
                "Configurar host e porta",
                f"PRG;{esn_4315};10;05#{host};06#{port};08#{host};09#{port}",
                "4315_host",
                esn_4315,
            )
            show_command("Configurar protocolo TCP", f"PRG;{esn_4315};10;07#00;10#00", "4315_tcp", esn_4315)
            show_command("Desabilitar parâmetro ZIP", f"PRG;{esn_4315};10;55#00", "4315_zip", esn_4315)

        with st.expander("Tempos de comunicação"):
            show_command(
                "Tempos padrão — 1 hora desligado e 2 minutos ligado",
                f"PRG;{esn_4315};16;70#3600;71#0;72#0;73#120;74#0;75#0;76#0;77#0;78#0;79#120;80#0;81#30;82#120;83#0;84#30;85#120;86#0;87#30",
                "4315_times_full",
                esn_4315,
            )
            show_command(
                "Tempos simplificados — ignição ligada/desligada",
                f"PRG;{esn_4315};16;70#3600;79#120",
                "4315_times_simple",
                esn_4315,
            )
            speed = st.number_input("Velocidade para alerta (km/h)", min_value=0, value=110, step=5, key="cmd_4315_speed")
            if speed > 0:
                show_command("Configurar excesso de velocidade", f"PRG;{esn_4315};16;21#{speed}", "4315_speed", esn_4315)

        with st.expander("Configuração de ignição"):
            show_command("Ignição física — pós-chave", f"PRG;{esn_4315};17;00#01", "4315_ignition_physical", esn_4315)
            show_command("Ignição virtual por acelerômetro", f"PRG;{esn_4315};17;00#03", "4315_ignition_accel", esn_4315)
            show_command("Ignição virtual por tensão", f"PRG;{esn_4315};17;00#02", "4315_ignition_voltage", esn_4315)
            voltage_1, voltage_2 = st.columns(2)
            high_voltage = voltage_1.number_input("Tensão para ligar — 13,2 V = 132", value=132, key="cmd_4315_voltage_high")
            low_voltage = voltage_2.number_input("Tensão para desligar — 12,8 V = 128", value=128, key="cmd_4315_voltage_low")
            show_command(
                "Ajustar tensão de ignição virtual",
                f"PRG;{esn_4315};17;15#{high_voltage};16#{low_voltage}",
                "4315_voltage_adjust",
                esn_4315,
            )

        with st.expander("Ações remotas"):
            show_command("Reiniciar equipamento", f"CMD;{esn_4315};03;03", "4315_reboot", esn_4315)
            show_command("Solicitar posição", f"CMD;{esn_4315};03;01", "4315_position", esn_4315)
            show_command("Ativar saída 1", f"CMD;{esn_4315};04;01", "4315_output_on", esn_4315)
            show_command("Desativar saída 1", f"CMD;{esn_4315};04;02", "4315_output_off", esn_4315)

        with st.expander("Configurações avançadas"):
            show_command(
                "Configurar string de dados",
                f"PRG;{esn_4315};10;80#00fff83f;82#00fff83f;84#00fff83f;86#00;87#00001ffbff;97#00",
                "4315_data_string",
                esn_4315,
            )
            show_command("Configuração global 1", f"PRG;{esn_4315};10;81#0007800f", "4315_global_1", esn_4315)
            show_command(
                "Configuração global 2",
                f"PRG;{esn_4315};11;00#02;01#01;02#00;03#50;04#00;05#00;06#00;07#00;08#00;09#00;10#00;11#00;12#00;13#00;14#00;40#01;41#02;42#06;43#00;44#00",
                "4315_global_2",
                esn_4315,
            )
            show_command(
                "Configuração global 3",
                f"PRG;{esn_4315};11;45#00;46#00;47#00;60#00;61#00;62#00;63#00;64#00;65#00;66#00;67#00",
                "4315_global_3",
                esn_4315,
            )
            odometer = st.number_input("Hodômetro em metros", min_value=0, max_value=1_000_000_000, step=1_000, key="cmd_4315_odometer")
            if odometer > 0:
                show_command("Ajustar hodômetro", f"CMD;{esn_4315};05;03;{odometer}", "4315_odometer", esn_4315)

        with st.expander("Configurações para motocicletas"):
            show_command("Configuração moto 1", f"PRG;{esn_4315};10;60#0;70#00", "4315_motorcycle_1", esn_4315)
            show_command("Configuração moto 2", f"PRG;{esn_4315};19;00#02;01#0.10", "4315_motorcycle_2", esn_4315)
            show_command("Configuração moto 3", f"PRG;{esn_4315};19;01", "4315_motorcycle_3", esn_4315)
            show_command("Configuração moto 4", f"PRG;{esn_4315};17;01#120", "4315_motorcycle_4", esn_4315)
            show_command("Configuração moto 5", f"PRG;{esn_4315};16;70#0", "4315_motorcycle_5", esn_4315)

if st.button("Limpar campos"):
    for key in list(st.session_state):
        if key.startswith("cmd_"):
            st.session_state.pop(key, None)
    st.rerun()
