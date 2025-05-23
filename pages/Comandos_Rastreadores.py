# pages/Comandos_Rastreadores.py
import streamlit as st # Import principal

# 1. st.set_page_config() DEVE SER O PRIMEIRO COMANDO STREAMLIT
# Mova qualquer configuração de página para o topo.
# É importante notar que st.set_page_config() só pode ser chamado uma vez por página.
# Se você já tem um no seu Simulador_Comercial.py para a página principal,
# você PODE ou NÃO PODE precisar dele em cada subpágina, dependendo
# se você quer configurações diferentes para cada página do menu.
# Se você quer um layout global, defina apenas no script principal.
# Se cada página tiver um título de aba diferente, você precisará dele aqui.

# Tente remover o st.set_page_config das subpáginas se você já configurou globalmente
# no Simulador_Comercial.py e não precisa de títulos de aba ou layouts diferentes.
# Se precisar de títulos de aba diferentes para cada página, mantenha-o, mas garanta que é o primeiro.

# ASSUMINDO QUE VOCÊ QUER UM TÍTULO DE ABA DIFERENTE PARA ESTA PÁGINA:

# 2. AGORA o bloco de Verificação de Autenticação
if st.session_state.get("authentication_status", False) is not True:
    st.error("🔒 Acesso Negado! Por favor, faça login na página principal para continuar.")
    # st.page_link("Simulador_Comercial.py", label="Ir para Login", icon="🏠") # Use st.page_link para navegação
    st.stop()

# 3. Restante dos imports específicos da página (se houver) e o código da página
# import pandas as pd # Exemplo
# from utils_rastreadores import ... # Exemplo

st.title("Comandos para Rastreadores")
st.write(f"Usuário: {st.session_state.get('name', 'N/A')} ({st.session_state.get('username', 'N/A')})")
st.write(f"Nível de Acesso: {st.session_state.get('role', 'Indefinido')}")
st.markdown("---")

# ... resto do código da página Comandos_Rastreadores.py ...


# 🛠️ Configuração da página
st.set_page_config(
    layout="wide",
    page_title="Simulador de Comandos Suntech e-Trac",
    page_icon="imgs/v-c.png",
    initial_sidebar_state="expanded"
)

# 🔵 Logotipo e cabeçalho estilizado
st.image("imgs/logo.png", width=250)
st.markdown("<h1 style='text-align: center; color: #54A033;'>Simulador de Comandos Suntech e-Trac</h1>", unsafe_allow_html=True)
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
            st.success("✅ Comando gerado:")
            st.text("IP, PORT e APN e-Trac")
            apn = st.text_input("Digite a APN personalizada:", value="allcom.claro.com.br", key="apn")

            left_column, right_column = st.columns(2)
            with left_column:
                user = st.text_input("Digite o Usuário:", value="allcom", key="user")
            with right_column:
                password = st.text_input("Digite a Senha:", value="allcom", key="password", type="password")


            st.code(f"ST300NTW;{serial};02;1;{apn};{user};{password};54.94.190.167;9601;35.198.41.183;9601;;")
            st.text("Disable ZIP")
            st.code(f'ST300SVC;{serial};02;1;180;0;0;0;1;1;0;1;0;0;1;0')
            st.text("Protocolo TCP/IP")
            st.code(f'ST300ADP;{serial};02;T;T;1;;0;0;0;0;0;0')
            st.text("Intervalos de Envio Carro")
            st.code(f'ST300RPT;{serial};02;3600;120;3600;1;0;600;0;0;0')
            st.text("Intervalos de Envio Moto")
            st.code(f'ST300RPT;{serial};02;0;60;0;1;0;0;0;0;0')
            st.text("Eventos")
            st.code(f'ST300EVT;{serial};02;0;10;0;12;3;9;30;20;0;1;7;1;1;0;0;0;0;0;0;9;9;0;0;0')
            st.text("NPTs")
            st.code(f'ST300NPT;{serial};02;20.0;1;30;0;1;500;300;5;10;100;10;180;100;1')

        elif mod_rastreador == 'ST4315':
            st.subheader("📜 Comandos disponíveis")
            st.success("✅ Comando gerado:")
            st.text("APN Allcom Vivo")
            apn = st.text_input("Digite a APN personalizada:", value="allcomiot.vivo.com.br", key="apn")
            left_column, right_column = st.columns(2)
            with left_column:
                user = st.text_input("Digite o Usuário:", value="allcom", key="user")
            with right_column:
                password = st.text_input("Digite a Senha:", value="allcom", key="password", type="password")
            st.code(f'PRG;{serial};10;00#01;01#{apn};02#{user};03#{password}')
            st.text("IP e PORT e-Trac")
            st.code(f'PRG;{serial};10;05#54.94.190.167;06#9601;08#54.94.190.167;09#9601')
            st.text("Protocolo TCP")
            st.code(f'PRG;{serial};10;07#00;10#00')
            st.text("ZIP Desabilittado")
            st.code(f'PRG;{serial};10;55#00')
            st.text("Ignição Física")
            st.code(f'PRG;{serial};17;00#01')
            st.text("Ignição Virtual Acelerometro")
            st.code(f'PRG;{serial};17;00#03')
            st.text("Reboot > Reiniciar")
            st.code(f'CMD;{serial};03;03')
            st.text("StatusReq > Solicitar posição")
            st.code(f'CMD;{serial};03;01')

            st.text("Limite de velocidade em km/h")
            velocidade = st.text_input("Digite a velocidade máxima: ")
            st.code(f'PRG;{serial};16;21#{velocidade}')

            st.text("Intervalos e ângulo")
            igon = st.text_input("Intervalo Ligado (em Segundos):")
            igoff = st.text_input("Intervalo Desligado (em Segundos):")
            ang = st.text_input("Ângulo:")
            st.code(f'PRG;{serial};16;70#{igoff};71#0;72#0;73#{igon};74#0;75#0;76#0;77#0;78#0;79#120;80#0;81#{ang};82#120;83#0;84#{ang};85#120;86#0;87#{ang}')

        elif mod_rastreador == 'ST300HD':
            st.subheader("📜 Comandos disponíveis")
            st.success("✅ Comando gerado:")

            st.text("Adicionar motorista")
            idM = st.text_input("Digite o Número do Motorista: ")
            ibutton = st.text_input("Digite o Serial do Ibutton: ")
            st.code(f'ST300HAD;{serial};02;{idM};{ibutton}')

            st.text("Remover motorista")
            st.code(f'ST300HRD;{serial};02;{idM}')



# 🔄 Botão para reiniciar
if st.button("🔄 Reiniciar"):
    st.rerun()
