# Exemplo para: pages/Simulador_PF.py (e outros arquivos em pages/)
# pages/Simulador_Licitação.py
import streamlit as st
from decimal import Decimal, ROUND_DOWN
# Adicione quaisquer outras importações que esta página específica precise (ex: pandas, numpy, etc.)
# import pandas as pd

# 1. st.set_page_config() - PRIMEIRO COMANDO STREAMLIT
# Ajuste page_title e page_icon para cada página específica.
st.set_page_config(
    layout="wide",
    page_title="Simulador Licitação", 
    page_icon="📝", # Exemplo de ícone, você pode usar o seu "imgs/v-c.png" se o caminho estiver correto
    initial_sidebar_state="expanded"
)

# 2. BLOCO DE VERIFICAÇÃO DE AUTENTICAÇÃO
# Este bloco garante que apenas usuários logados acessem a página.
auth_status = st.session_state.get("authentication_status", False)
if auth_status is not True: # Checagem explícita contra True
    st.error("🔒 Acesso Negado! Por favor, faça login na página principal para continuar.")
    # Adiciona um print para os logs do Streamlit Cloud para ajudar na depuração
    print(f"ACCESS_DENIED_LOG (Simulador_Licitação.py): User not authenticated. Status: {auth_status}")
    # Tenta usar st.page_link, com fallback se não disponível (versões antigas do Streamlit)
    try:
        # Certifique-se que o nome do arquivo da página principal está correto aqui
        st.page_link("Simulador_Comercial.py", label="Ir para Login", icon="🏠")
    except AttributeError: # st.page_link pode não existir em versões mais antigas
        st.info("Retorne à página principal para efetuar o login.")
    st.stop() # Impede a execução do restante da página

# Se chegou aqui, o usuário está autenticado.
current_username = st.session_state.get('username', 'N/A')
current_role = st.session_state.get('role', 'Indefinido')
current_name = st.session_state.get('name', 'N/A')

# Adiciona um print para os logs do Streamlit Cloud
print(f"INFO_LOG (Simulador_Licitação.py): User '{current_username}' authenticated. Role: '{current_role}'")

# 3. Restante do código da sua página
# (Cole aqui o conteúdo específico da sua página Simulador_Licitação.py)

# Exemplo de como você pode iniciar o conteúdo da página:
# try:
#     st.image("imgs/logo.png", width=250) # Verifique o caminho para 'imgs/logo.png'
# except FileNotFoundError:
#     print(f"WARN_LOG (Simulador_Licitação.py): Arquivo imgs/logo.png não encontrado.")
# except Exception as e_img:
#     print(f"WARN_LOG (Simulador_Licitação.py): Erro ao carregar imgs/logo.png: {e_img}")


st.markdown("<h1 style='text-align: center; color: #00447C;'>Simulador de Licitação</h1>", unsafe_allow_html=True) # Cor exemplo
st.markdown("---")

st.write(f"Usuário: {current_name} ({current_username})")
st.write(f"Nível de Acesso: {current_role}")
st.markdown("---")

# 🔵 Logotipo e cabeçalho estilizado
st.image("imgs/logo.png", width=250)
st.markdown("<h1 style='text-align: center; color: #54A033;'>Simulador para Licitações e Editais</h1>", unsafe_allow_html=True)
st.markdown("---")

# 📌 Tabela de preços convertida para Decimal
precoCusto = {
    "Rastreador GPRS/GSM 2G": Decimal("300"),
    "Rastreador GPRS/GSM 4G": Decimal("400"),
    "Rastreador Satelital": Decimal("900"),
    "Telemetria/CAN": Decimal("600"),
    "RFID - ID Motorista": Decimal("153"),
}

# 🎯 Sidebar para entrada de dados
st.sidebar.header("📝 Configurações")
qtd = Decimal(st.sidebar.number_input("Quantidade de Veículos 🚗", min_value=1, value=1, step=1))
contrato = Decimal(st.sidebar.number_input("Tempo de Contrato (meses) 📆", min_value=1, value=12, step=1))

# 📌 Margem de lucro
margem = Decimal(str(st.sidebar.slider("Margem de Lucro (%) 📈", min_value=0.0, max_value=1.0, value=0.3, step=0.01, format="%.2f")))

# 🔽 Seleção de itens (distribuídos em 2 colunas)
st.markdown("### 📦 Selecione os Itens:")
col1, col2 = st.columns(2)
itens_selecionados = []

for idx, (item, preco) in enumerate(precoCusto.items()):
    col = col1 if idx % 2 == 0 else col2
    with col:
        toggle = st.toggle(f"{item} - R$ {preco:,.2f}")  # ✅ Nome e preço juntos
        if toggle:
            itens_selecionados.append(item)

# 📌 Cálculo do valor total
if itens_selecionados:
    valor_total_unitario = sum(precoCusto[item] for item in itens_selecionados)
    un_contrato = (valor_total_unitario / Decimal(12)).quantize(Decimal('0.01'), rounding=ROUND_DOWN)
    un_margem = (un_contrato + (un_contrato * margem)).quantize(Decimal('0.01'), rounding=ROUND_DOWN)
    valor_total = (un_margem * qtd * contrato).quantize(Decimal('0.01'), rounding=ROUND_DOWN)

    # 🔹 Exibição dos resultados
    st.success("✅ Cálculo realizado com sucesso!")
    st.info(f"💰 **Valor Unitário:** R$ {un_margem}")
    st.info(f"📄 **Valor Total do Contrato:** R$ {valor_total}")
    st.write(f"##### (considerando {qtd} veículos e {contrato} meses)")
else:
    st.warning("⚠️ Selecione pelo menos um item para calcular o valor total.")

# 🎯 Botão para limpar seleção
if st.button("🔄 Limpar Seleção"):
    st.rerun()
