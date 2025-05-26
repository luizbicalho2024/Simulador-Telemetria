# Exemplo para: pages/Simulador_PF.py (e outros arquivos em pages/)
import streamlit as st

# 2. BLOCO DE VERIFICAÇÃO DE AUTENTICAÇÃO
# Este bloco deve vir DEPOIS de st.set_page_config e ANTES de qualquer outro st.* comando.
if st.session_state.get("authentication_status", False) is not True:
    st.error("🔒 Acesso Negado! Por favor, faça login na página principal para continuar.")
    # Considere adicionar um link para a página de login se desejar:
    # st.page_link("Simulador_Comercial.py", label="Ir para Login", icon="🏠")
    st.stop() # Impede a execução do restante da página se não estiver autenticado

# --- Restante do código da sua página ---
st.title(f"Simulador Pessoa Física (Acessado por: {st.session_state.get('name', 'Usuário')})")
# ... seu código específico para esta página ...

# Exemplo de verificação de papel (role) se necessário dentro de uma página específica:
# if st.session_state.get("role") == "admin":
#     st.write("Conteúdo específico para Admin nesta página.")
# elif st.session_state.get("role") == "user":
#     st.write("Conteúdo específico para Usuário Comum nesta página.")
# else:
#     st.warning("Papel do usuário não definido.")

from decimal import Decimal, ROUND_DOWN

# 🛠️ Configuração da página
st.set_page_config(
    layout="wide",
    page_title="Licitações e Editais",
    page_icon="imgs/v-c.png",
    initial_sidebar_state="expanded"
)

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
