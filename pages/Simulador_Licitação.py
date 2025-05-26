# pages/Simulador_Licitação.py
from decimal import Decimal, ROUND_DOWN # Importações Python primeiro
import streamlit as st

# 1. st.set_page_config() - PRIMEIRO COMANDO STREAMLIT
st.set_page_config(
    layout="wide",
    page_title="Simulador Licitações e Editais", # Título da aba específico
    page_icon="imgs/v-c.png", # Verifique se o caminho está correto
    initial_sidebar_state="expanded"
)

# 2. BLOCO DE VERIFICAÇÃO DE AUTENTICAÇÃO
auth_status = st.session_state.get("authentication_status", False)
if auth_status is not True:
    st.error("🔒 Acesso Negado! Por favor, faça login na página principal para continuar.")
    print(f"ACCESS_DENIED_LOG (Simulador_Licitação.py): User not authenticated. Status: {auth_status}")
    try:
        st.page_link("Simulador_Comercial.py", label="Ir para Login", icon="🏠")
    except AttributeError: 
        st.info("Retorne à página principal para efetuar o login.")
    st.stop() 

# Se chegou aqui, o usuário está autenticado.
current_username = st.session_state.get('username', 'N/A')
current_role = st.session_state.get('role', 'Indefinido') # Será 'Indefinido' se não for pego corretamente no login
current_name = st.session_state.get('name', 'N/A')

print(f"INFO_LOG (Simulador_Licitação.py): User '{current_username}' authenticated. Role: '{current_role}'")

# 3. Restante do código da sua página
try:
    st.image("imgs/logo.png", width=250) # Verifique o caminho
except FileNotFoundError:
    print("WARN_LOG (Simulador_Licitação.py): Arquivo imgs/logo.png não encontrado.")
except Exception as e_img:
    print(f"WARN_LOG (Simulador_Licitação.py): Erro ao carregar imgs/logo.png: {e_img}")

st.markdown("<h1 style='text-align: center; color: #54A033;'>Simulador para Licitações e Editais</h1>", unsafe_allow_html=True)
st.markdown("---")

st.write(f"Usuário: {current_name} ({current_username})")
st.write(f"Nível de Acesso: {current_role}") # Se estiver "Indefinido", o problema está no Simulador_Comercial.py ao definir st.session_state.role
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
st.sidebar.header("📝 Configurações da Licitação") # Título mais específico
qtd = Decimal(st.sidebar.number_input("Quantidade de Veículos 🚗", min_value=1, value=1, step=1, key="lic_qtd_veiculos"))
contrato = Decimal(st.sidebar.number_input("Tempo de Contrato (meses) 📆", min_value=1, value=12, step=1, key="lic_tempo_contrato"))

# 📌 Margem de lucro
margem = Decimal(str(st.sidebar.slider("Margem de Lucro (%) 📈", min_value=0.0, max_value=1.0, value=0.3, step=0.01, format="%.2f", key="lic_margem_lucro")))

# 🔽 Seleção de itens (distribuídos em 2 colunas)
st.markdown("### 📦 Selecione os Itens da Licitação:")
col1, col2 = st.columns(2)
itens_selecionados = []

# Usar um loop para criar os toggles com chaves únicas
for idx, (item, preco) in enumerate(precoCusto.items()):
    col_target = col1 if idx % 2 == 0 else col2
    with col_target:
        # Chave única para cada toggle
        item_key = f"toggle_item_lic_{item.replace(' ', '_').replace('/', '_')}" 
        if st.toggle(f"{item} - R$ {preco:,.2f}", key=item_key):
            itens_selecionados.append(item)

# 📌 Cálculo do valor total
if itens_selecionados:
    valor_total_unitario = sum(precoCusto[item] for item in itens_selecionados)
    # Divisão por 12 para mensalidade, se for o caso, ou ajuste a lógica de cálculo conforme necessidade
    mensalidade_custo_unitario = (valor_total_unitario / Decimal(12)).quantize(Decimal('0.01'), rounding=ROUND_DOWN) 
    mensalidade_venda_unitaria = (mensalidade_custo_unitario * (Decimal(1) + margem)).quantize(Decimal('0.01'), rounding=ROUND_DOWN)
    
    valor_total_contrato_global = (mensalidade_venda_unitaria * qtd * contrato).quantize(Decimal('0.01'), rounding=ROUND_DOWN)

    # 🔹 Exibição dos resultados
    st.success("✅ Cálculo da Proposta para Licitação realizado!")
    st.metric(label="Mensalidade por Veículo (com margem)", value=f"R$ {mensalidade_venda_unitaria:,.2f}")
    st.metric(label="Valor Total Estimado do Contrato", value=f"R$ {valor_total_contrato_global:,.2f}")
    st.caption(f"Cálculo considerando {qtd} veículo(s) por {contrato} meses, com margem de {margem*100:.0f}%.")
else:
    st.warning("⚠️ Selecione pelo menos um item para calcular a proposta.")

# 🎯 Botão para limpar seleção (reinicia a página)
if st.button("🔄 Limpar Campos e Recalcular", key="lic_btn_limpar_recalcular"):
    # Limpar os st.toggle é mais complexo pois o estado é gerenciado pelo Streamlit.
    # A forma mais simples de "limpar" é forçar um rerun, que re-renderiza com os valores default.
    # Para um reset mais granular, você teria que gerenciar o estado de cada toggle em st.session_state.
    st.rerun()