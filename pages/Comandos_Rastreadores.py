import streamlit as st

# 🛠️ Configuração da página
st.set_page_config(
    layout="wide",
    page_title="Simulador de Comandos Suntech e-Trac",
    page_icon="🛰️",
    initial_sidebar_state="expanded"
)

# 🔵 Logotipo e cabeçalho estilizado
st.image("imgs/logo.png", width=250)
st.markdown("<h1 style='text-align: center; color: #004aad;'>🛰️ Simulador de Comandos Suntech e-Trac</h1>", unsafe_allow_html=True)
st.markdown("---")

# 🎯 Sidebar para entrada de dados
st.sidebar.header("🔧 Configuração do Simulador")
serial = st.sidebar.text_input("📟 Insira o Serial:", value="XXXXXXX", key="serial")

# 📌 Layout de duas colunas para organização
left_column, right_column = st.columns(2)

with left_column:
    st.subheader("📡 Selecione o Modelo")
    mod_rastreador = st.radio(
        'Modelos disponíveis:',
        ("ST310U", "ST4315", "ST300HD")
    )

if not serial or serial == "XXXXXXX":
    st.warning("⚠️ Insira um serial válido para gerar os comandos.")

else:
    with right_column:
        if mod_rastreador == 'ST310U':
            st.subheader("📜 Escolha o Comando")
            comandos = st.radio(
                'Comandos disponíveis:',
                ("IP e APN Suntech e-Trac", "Disable ZIP", "Protocolo TCP/IP", 'Tempo de Comunicação', 'Eventos', 'NPTs')
            )

            if comandos == "IP e APN Suntech e-Trac":
                apns = st.radio(
                    '🌐 Escolha a APN:',
                    ("Allcom", "M2data", "Virtueyes")
                )

                apn_dict = {
                    "Allcom": "allcom.claro.com.br;allcom;allcom",
                    "M2data": "m2data.claro.com.br;claro;claro",
                    "Virtueyes": "virtueyes.claro.com.br;veye;veye"
                }

                st.success("✅ Comando gerado:")
                st.code(f"ST300NTW;{serial};02;1;{apn_dict[apns]};54.94.190.167;9601;35.198.41.183;9601;;")

            elif comandos == "Disable ZIP":
                st.success("✅ Comando gerado:")
                st.code(f'ST300SVC;{serial};02;1;180;0;0;0;1;1;0;1;0;0;1;0')

            elif comandos == 'Protocolo TCP/IP':
                st.success("✅ Comando gerado:")
                st.code(f'ST300ADP;{serial};02;T;T;1;;0;0;0;0;0;0')

            elif comandos == 'Tempo de Comunicação':
                veiculo = st.radio(
                    '🚗 Tipo de Veículo:',
                    ("Carro", "Moto")
                )

                comando_tempo = {
                    "Carro": f'ST300RPT;{serial};02;3600;120;3600;1;0;600;0;0;0',
                    "Moto": f'ST300RPT;{serial};02;0;60;3600;1;0;0;0;0;0'
                }

                st.success("✅ Comando gerado:")
                st.code(comando_tempo[veiculo])

            elif comandos == "Eventos":
                st.success("✅ Comando gerado:")
                st.code(f'ST300EVT;{serial};02;0;10;0;12;3;9;30;20;0;1;7;1;1;0;0;0;0;0;0;9;9;0;0;0')

            elif comandos == "NPTs":
                st.success("✅ Comando gerado:")
                st.code(f'ST300NPT;{serial};02;20.0;1;30;0;1;500;300;5;10;100;10;180;100;1')

        elif mod_rastreador == 'ST4315':
            st.subheader("📜 Comandos disponíveis")
            st.success("✅ Comando gerado:")
            st.code(f'RPR;{serial};OK;10;00#00;01#allcomiot.vivo.com.br;02#allcom;03#allcom;04#;05#54.94.190.167;06#9601;07#00;08#54.94.190.167;09#9601;10#00;11#0;12#0;13#00;60#600;70#01;71#600;61#00;62#500;63#300')
            st.code(f'RPR;{serial};OK;10;55#00;58#03;64#00;50#30;51#0;72#00;73#')

# 🔄 Botão para reiniciar
if st.button("🔄 Reiniciar"):
    st.rerun()
