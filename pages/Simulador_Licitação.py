import streamlit as st
from decimal import Decimal, ROUND_DOWN

# 🛠️ Configuração da página
st.set_page_config(
    layout="wide",
    page_title="Licitações e Editais",
    page_icon="📜",
    initial_sidebar_state="expanded"
)

# 🔵 Logotipo e cabeçalho estilizado
st.image("imgs/logo.png", width=250)
st.markdown("<h1 style='text-align: center; color: #004aad;'>📜 Simulador para Licitações e Editais</h1>", unsafe_allow_html=True)
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

# Criar dicionário para armazenar seleção de cada item
selecionados = {item: False for item in precoCusto.keys()}

# Estilos CSS para os botões
st.markdown("""
    <style>
        .item-box {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px;
            border: 2px solid #004aad;
            border-radius: 10px;
            background-color: #f8f9fa;
            cursor: pointer;
            margin-bottom: 10px;
            transition: all 0.3s ease-in-out;
            font-weight: bold;
        }
        .item-box:hover {
            background-color: #e0f2ff;
        }
        .item-box.selected {
            background-color: #28a745 !important; /* Verde quando selecionado */
            color: white !important;
            border-color: #1e7e34;
        }
        .item-price {
            font-weight: bold;
            color: green;
        }
    </style>
""", unsafe_allow_html=True)

# Lista de itens selecionados
itens_selecionados = st.session_state.get("itens_selecionados", set())

for idx, (item, preco) in enumerate(precoCusto.items()):
    col = col1 if idx % 2 == 0 else col2
    with col:
        # Controla se o item foi selecionado
        is_selected = item in itens_selecionados
        button_style = "selected" if is_selected else ""

        # Criando um botão clicável
        if st.button(
            f"{item} - R$ {preco:,.2f}",
            key=item,
            help="Clique para selecionar ou desselecionar",
        ):
            if is_selected:
                itens_selecionados.remove(item)  # Remove se já estiver selecionado
            else:
                itens_selecionados.add(item)  # Adiciona se não estiver selecionado
            st.session_state.itens_selecionados = itens_selecionados
            st.rerun()  # Atualiza a página para refletir mudanças

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
    st.session_state.itens_selecionados = set()
    st.rerun()
