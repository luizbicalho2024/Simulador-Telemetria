# Exemplo para: pages/Simulador_PF.py (e outros arquivos em pages/)
import streamlit as st

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

# 🛠️ Configuração da página
st.set_page_config(
    layout="wide",
    page_title="Simulador PF",
    page_icon="imgs/v-c.png",
    initial_sidebar_state="expanded"
)

# 2. BLOCO DE VERIFICAÇÃO DE AUTENTICAÇÃO
# Este bloco deve vir DEPOIS de st.set_page_config e ANTES de qualquer outro st.* comando.
if st.session_state.get("authentication_status", False) is not True:
    st.error("🔒 Acesso Negado! Por favor, faça login na página principal para continuar.")
    # Considere adicionar um link para a página de login se desejar:
    # st.page_link("Simulador_Comercial.py", label="Ir para Login", icon="🏠")
    st.stop() # Impede a execução do restante da página se não estiver autenticado


# 🔵 Logotipo e cabeçalho estilizado
st.image("imgs/logo.png", width=250)
st.markdown("<h1 style='text-align: center; color: #54A033;'>Simulador de Venda - Pessoa Física</h1>", unsafe_allow_html=True)
st.markdown("---")

# 📌 Definição dos preços
precos = {
    "GPRS / Gsm": 970.56,
    "Satelital": 2325.60
}

# 🎯 Seção de entrada de dados
st.sidebar.header("📝 Configurações")
modeloPF = st.sidebar.selectbox("Tipo de Rastreador 📡", list(precos.keys()))

# 🔢 Exibir preço à vista
preco_base = precos[modeloPF]
st.markdown(f"### 💰 Valor Anual À Vista: R$ {preco_base:,.2f}")

# 🔽 Opção de desconto
st.markdown("### 🎯 Aplicar Desconto:")
col1, col2 = st.columns([1, 3])
desconto = col1.checkbox("Ativar", value=False)
if desconto:
    porcetagem = col2.number_input("Percentual (%)", min_value=0, max_value=100, value=0, step=1)
    desconto_calc = preco_base - (preco_base * (porcetagem / 100))
    st.success(f"✅ {porcetagem}% de desconto aplicado!")
    st.info(f"💰 **Valor com Desconto:** R$ {desconto_calc:,.2f}")
else:
    desconto_calc = preco_base

# 🔽 Opção de parcelamento
st.markdown("### 💳 Parcelamento:")
parcelamento = st.checkbox("Ativar", value=False, key="parcelamento_pf")

if parcelamento:
    num_parcelas = st.selectbox("Quantidade de Parcelas:", [i for i in range(2, 13)])
    margem = num_parcelas * 0.0408
    valor_parcela = (desconto_calc / num_parcelas) * (1 + margem)
    total_parcelado = valor_parcela * num_parcelas

    st.success(f"✅ Parcelado em {num_parcelas}x")
    st.info(f"📄 **{num_parcelas} Parcelas de:** R$ {valor_parcela:,.2f}")
    st.markdown(f"### 💰 Valor Total Parcelado: R$ {total_parcelado:,.2f}")

# 🎯 Botão para limpar seleção
if st.button("🔄 Limpar Seleção"):
    st.rerun()
