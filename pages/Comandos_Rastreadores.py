import streamlit as st

# 1. st.set_page_config() DEVE SER O PRIMEIRO COMANDO STREAMLIT
# Esta configuração é específica para esta página.
st.set_page_config(
    layout="wide",
    page_title="Comandos Suntech e-Trac", # Título da aba do navegador para esta página
    page_icon="imgs/v-c.png", # Verifique se este caminho está correto relativo à raiz do projeto
    initial_sidebar_state="expanded"
)

# 2. BLOCO DE VERIFICAÇÃO DE AUTENTICAÇÃO
# Este bloco deve vir DEPOIS de st.set_page_config e ANTES de qualquer outro st.* comando.
if st.session_state.get("authentication_status", False) is not True:
    st.error("🔒 Acesso Negado! Por favor, faça login na página principal para continuar.")
    # Considere adicionar um link para a página de login se desejar:
    # st.page_link("Simulador_Comercial.py", label="Ir para Login", icon="🏠")
    st.stop() # Impede a execução do restante da página se não estiver autenticado

# Se chegou aqui, o usuário está autenticado.
# Agora você pode ter outros imports específicos da página ou começar o layout.

# 3. Restante do código da página
# 🔵 Logotipo e cabeçalho estilizado
# Verifique se o caminho para "imgs/logo.png" está correto a partir da raiz do projeto.
# Se a pasta 'imgs' estiver na raiz do projeto, o caminho está ok.
try:
    st.image("imgs/logo.png", width=250)
except FileNotFoundError:
    st.error("Erro: Arquivo de logo 'imgs/logo.png' não encontrado. Verifique o caminho.")

st.markdown("<h1 style='text-align: center; color: #54A033;'>Simulador de Comandos Suntech e-Trac</h1>", unsafe_allow_html=True)
st.markdown("---")

# Informações do usuário logado (exemplo)
st.write(f"Usuário: {st.session_state.get('name', 'N/A')} ({st.session_state.get('username', 'N/A')})")
st.write(f"Nível de Acesso: {st.session_state.get('role', 'Indefinido')}") # "Indefinido" aqui ainda é um problema se o login foi bem sucedido.
st.markdown("---")


# 🎯 Sidebar para entrada de dados
st.sidebar.header("🔧 Configuração do Simulador")
serial = st.sidebar.text_input("📟 Insira o Serial:", value="XXXXXXX", key="serial_rastreador") # Adicionada chave única

# 📌 Layout de duas colunas para organização
left_column, right_column = st.columns(2)

with left_column:
    st.subheader("📡 Selecione o Modelo")
    mod_rastreador = st.radio(
        'Modelos disponíveis:',
        ("ST310U", "ST4315", "ST300HD"),
        key="mod_rastreador_radio" # Adicionada chave única
    )

if not serial or serial == "XXXXXXX":
    st.warning("⚠️ Insira um serial válido para gerar os comandos.")
else:
    with right_column:
        if mod_rastreador == 'ST310U':
            st.subheader("📜 Escolha o Comando")
            # Inputs para ST310U
            apn = st.text_input("Digite a APN personalizada:", value="allcom.claro.com.br", key="apn_st310u")
            
            # Subcolunas dentro da right_column para user e password
            sub_left, sub_right = st.columns(2)
            with sub_left:
                user = st.text_input("Digite o Usuário:", value="allcom", key="user_st310u")
            with sub_right:
                password = st.text_input("Digite a Senha:", value="allcom", key="password_st310u", type="password")

            st.success("✅ Comandos gerados para ST310U:")
            st.text("IP, PORT e APN e-Trac")
            st.code(f"ST300NTW;{serial};02;1;{apn};{user};{password};54.94.190.167;9601;35.198.41.183;9601;;")
            st.text("Disable ZIP")
            st.code(f'ST300SVC;{serial};02;1;180;0;0;0;1;1;0;1;0;0;1;0')
            # ... (restante dos comandos para ST310U) ...
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
            st.subheader("📜 Comandos disponíveis para ST4315")
            # Inputs para ST4315
            apn_st4315 = st.text_input("Digite a APN personalizada:", value="allcomiot.vivo.com.br", key="apn_st4315")
            sub_left_4315, sub_right_4315 = st.columns(2)
            with sub_left_4315:
                user_st4315 = st.text_input("Digite o Usuário:", value="allcom", key="user_st4315")
            with sub_right_4315:
                password_st4315 = st.text_input("Digite a Senha:", value="allcom", key="password_st4315", type="password")
            
            velocidade_st4315 = st.text_input("Digite a velocidade máxima:", key="vel_st4315")
            igon_st4315 = st.text_input("Intervalo Ligado (em Segundos):", key="igon_st4315")
            igoff_st4315 = st.text_input("Intervalo Desligado (em Segundos):", key="igoff_st4315")
            ang_st4315 = st.text_input("Ângulo:", key="ang_st4315")

            st.success("✅ Comandos gerados para ST4315:")
            st.text("APN")
            st.code(f'PRG;{serial};10;00#01;01#{apn_st4315};02#{user_st4315};03#{password_st4315}')
            # ... (restante dos comandos para ST4315) ...
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
            st.code(f'PRG;{serial};16;21#{velocidade_st4315}')
            st.text("Intervalos e ângulo")
            st.code(f'PRG;{serial};16;70#{igoff_st4315};71#0;72#0;73#{igon_st4315};74#0;75#0;76#0;77#0;78#0;79#120;80#0;81#{ang_st4315};82#120;83#0;84#{ang_st4315};85#120;86#0;87#{ang_st4315}')


        elif mod_rastreador == 'ST300HD':
            st.subheader("📜 Comandos disponíveis para ST300HD")
            # Inputs para ST300HD
            idM_st300hd = st.text_input("Digite o Número do Motorista:", key="idm_st300hd")
            ibutton_st300hd = st.text_input("Digite o Serial do Ibutton:", key="ibutton_st300hd")

            st.success("✅ Comandos gerados para ST300HD:")
            st.text("Adicionar motorista")
            st.code(f'ST300HAD;{serial};02;{idM_st300hd};{ibutton_st300hd}')
            st.text("Remover motorista")
            st.code(f'ST300HRD;{serial};02;{idM_st300hd}') # Usa o mesmo idM para remover

# 🔄 Botão para reiniciar a página atual (apenas reroda o script da página)
if st.button("🔄 Reiniciar Campos da Página", key="btn_reiniciar_comandos"):
    st.rerun()