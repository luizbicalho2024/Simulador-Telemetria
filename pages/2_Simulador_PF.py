# pages/2_Simulador_PF.py
from decimal import Decimal, ROUND_DOWN
import streamlit as st

# --- 1. CONFIGURAÇÃO E AUTENTICAÇÃO ---
st.set_page_config(layout="wide", page_title="Simulador Pessoa Física", page_icon="imgs/v-c.png")

if not st.session_state.get("authentication_status"):
    st.error("🔒 Acesso Negado! Por favor, faça login.")
    st.stop()

# --- 2. CONSTANTES E DADOS ---
PRECOS = {"GPRS / Gsm": Decimal("970.56"), "Satelital": Decimal("2325.60")}
TAXAS_PARCELAMENTO = {
    2: Decimal("0.05"), 3: Decimal("0.065"), 4: Decimal("0.08"), 5: Decimal("0.09"),
    6: Decimal("0.10"), 7: Decimal("0.11"), 8: Decimal("0.12"), 9: Decimal("0.13"),
    10: Decimal("0.15"), 11: Decimal("0.16"), 12: Decimal("0.18")
}

# --- 3. INTERFACE PRINCIPAL ---
try:
    st.image("imgs/logo.png", width=250)
except Exception:
    pass

st.markdown("<h1 style='text-align: center; color: #54A033;'>Simulador de Venda - Pessoa Física</h1>", unsafe_allow_html=True)
st.markdown("---")
st.write(f"Usuário: {st.session_state.get('name', 'N/A')} ({st.session_state.get('username', 'N/A')})")
st.write(f"Nível de Acesso: {st.session_state.get('role', 'Indefinido').capitalize()}")
st.markdown("---")

st.sidebar.image("imgs/v-c.png", width=120)
st.sidebar.header("📝 Configurações PF")
modelo = st.sidebar.selectbox("Tipo de Rastreador 📡", list(PRECOS.keys()))
preco_base = PRECOS[modelo]
preco_final = preco_base

st.markdown(f"### 💰 Valor Anual À Vista: R$ {preco_base:,.2f}")

# --- Desconto ---
st.markdown("### 🎯 Aplicar Desconto:")
col1, col2 = st.columns([1, 3])
if col1.checkbox("Ativar Desconto"):
    percent_desconto = col2.number_input("Percentual (%)", min_value=0.0, max_value=100.0, step=1.0, format="%.2f")
    if percent_desconto > 0:
        desconto = (preco_base * (Decimal(str(percent_desconto)) / 100)).quantize(Decimal('0.01'), ROUND_DOWN)
        preco_final = preco_base - desconto
        st.success(f"Desconto de R$ {desconto:,.2f} aplicado!")

st.info(f"**Valor Final (com desconto):** R$ {preco_final:,.2f}")

# --- Parcelamento ---
st.markdown("### 💳 Parcelamento:")
if st.checkbox("Ativar Parcelamento"):
    num_parcelas = st.selectbox("Quantidade de Parcelas:", list(TAXAS_PARCELAMENTO.keys()))
    taxa_juros = TAXAS_PARCELAMENTO[num_parcelas]
    valor_com_juros = preco_final * (Decimal(1) + taxa_juros)
    valor_parcela = (valor_com_juros / num_parcelas).quantize(Decimal('0.01'), ROUND_DOWN)
    total_parcelado = valor_parcela * num_parcelas

    st.success(f"✅ Parcelado em {num_parcelas}x")
    st.markdown(f"#### {num_parcelas} Parcelas de: R$ {valor_parcela:,.2f}")
    st.markdown(f"#### Valor Total Parcelado: R$ {total_parcelado:,.2f}")
    st.caption(f"(Custo do parcelamento: R$ {total_parcelado - preco_final:,.2f})")
