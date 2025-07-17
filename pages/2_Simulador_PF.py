# pages/2_Simulador_PF.py
from decimal import Decimal, ROUND_DOWN
import streamlit as st
import user_management_db as umdb

st.set_page_config(layout="wide", page_title="Simulador Pessoa Física", page_icon="imgs/v-c.png")
if not st.session_state.get("authentication_status"):
    st.error("🔒 Acesso Negado!"); st.stop()

pricing_config = umdb.get_pricing_config()
PRECOS_PF = {k: Decimal(str(v)) for k, v in pricing_config.get("PRECOS_PF", {}).items()}
TAXAS_PARCELAMENTO_PF = {k: Decimal(str(v)) for k, v in pricing_config.get("TAXAS_PARCELAMENTO_PF", {}).items()}

st.sidebar.image("imgs/v-c.png", width=120)
if st.sidebar.button("🧹 Limpar Campos", use_container_width=True, key="pf_clear"):
    keys_to_clear = [k for k in st.session_state if k.startswith("pf_")]
    for k in keys_to_clear: del st.session_state[k]
    st.toast("Campos limpos!", icon="✨"); st.rerun()

try:
    st.image("imgs/logo.png", width=250)
except: pass

st.markdown("<h1 style='text-align: center; color: #54A033;'>Simulador de Venda - Pessoa Física</h1>", unsafe_allow_html=True)
st.markdown("---")
st.write(f"Usuário: {st.session_state.get('name', 'N/A')} ({st.session_state.get('username', 'N/A')})")
st.write(f"Nível de Acesso: {st.session_state.get('role', 'Indefinido').capitalize()}")
st.markdown("---")

st.sidebar.header("📝 Configurações PF")
modelo = st.sidebar.selectbox("Tipo de Rastreador 📡", list(PRECOS_PF.keys()), key="pf_modelo")
preco_base = PRECOS_PF.get(modelo, Decimal("0"))
preco_final = preco_base

st.markdown(f"### 💰 Valor Anual À Vista: R$ {preco_base:,.2f}")

st.markdown("### 🎯 Aplicar Desconto:")
col1, col2 = st.columns([1, 3])
if col1.checkbox("Ativar Desconto", key="pf_desconto_check"):
    percent_desconto = col2.number_input("Percentual (%)", min_value=0.0, max_value=100.0, step=1.0, format="%.2f", key="pf_desconto_percent")
    if percent_desconto > 0:
        desconto = (preco_base * (Decimal(str(percent_desconto)) / 100)).quantize(Decimal('0.01'), ROUND_DOWN)
        preco_final = preco_base - desconto
        st.success(f"Desconto de R$ {desconto:,.2f} aplicado!")

st.info(f"**Valor Final (com desconto):** R$ {preco_final:,.2f}")

st.markdown("### 💳 Parcelamento:")
if st.checkbox("Ativar Parcelamento", key="pf_parcela_check"):
    num_parcelas = st.selectbox("Quantidade de Parcelas:", list(TAXAS_PARCELAMENTO_PF.keys()), key="pf_num_parcelas")
    taxa_juros = TAXAS_PARCELAMENTO_PF.get(num_parcelas, Decimal("0"))
    valor_com_juros = preco_final * (Decimal(1) + taxa_juros)
    valor_parcela = (valor_com_juros / Decimal(num_parcelas)).quantize(Decimal('0.01'), ROUND_DOWN)
    total_parcelado = valor_parcela * Decimal(num_parcelas)

    st.success(f"✅ Parcelado em {num_parcelas}x")
    st.markdown(f"#### {num_parcelas} Parcelas de: R$ {valor_parcela:,.2f}")
    st.markdown(f"#### Valor Total Parcelado: R$ {total_parcelado:,.2f}")
    st.caption(f"(Custo do parcelamento: R$ {total_parcelado - preco_final:,.2f})")
