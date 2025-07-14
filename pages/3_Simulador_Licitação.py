# pages/3_Simulador_Licitação.py
from decimal import Decimal, ROUND_DOWN
import pandas as pd
import streamlit as st

# --- Bloco de Autenticação ---
st.set_page_config(layout="wide", page_title="Simulador Licitações")

if not st.session_state.get("authentication_status"):
    st.error("🔒 Acesso Negado! Por favor, faça login.")
    st.page_link("Simulador_Comercial.py", label="Ir para Login", icon="🏠")
    st.stop()

# --- Constantes e Configurações ---
PRECO_CUSTO = {
    "Rastreador GPRS/GSM 2G": Decimal("300"), "Rastreador GPRS/GSM 4G": Decimal("400"),
    "Rastreador Satelital": Decimal("900"), "Telemetria/CAN": Decimal("600"),
    "RFID - ID Motorista": Decimal("153"),
}
AMORTIZACAO_HARDWARE_MESES = Decimal("12")

# --- Interface ---
st.markdown("<h1 style='text-align: center; color: #54A033;'>Simulador para Licitações e Editais</h1>", unsafe_allow_html=True)
st.markdown("---")

st.sidebar.header("📝 Configurações da Licitação")
qtd = Decimal(st.sidebar.number_input("Qtd. de Veículos 🚗", min_value=1, value=1, step=1))
contrato = Decimal(st.sidebar.number_input("Tempo de Contrato (meses) 📆", min_value=12, value=12, step=12))
margem = Decimal(str(st.sidebar.slider("Margem de Lucro (%) 📈", 0, 100, 30))) / 100

st.sidebar.header("🔧 Custos de Serviços (Unitário)")
c_instalacao = Decimal(str(st.sidebar.number_input("Instalação", 0.0, value=50.0, step=10.0, format="%.2f")))
c_manutencao = Decimal(str(st.sidebar.number_input("Manutenção", 0.0, value=50.0, step=10.0, format="%.2f")))
c_desinstalacao = Decimal(str(st.sidebar.number_input("Desinstalação", 0.0, value=50.0, step=10.0, format="%.2f")))

col1, col2 = st.columns(2)
with col1:
    st.markdown("### 📦 Itens de Locação")
    itens_selecionados = [item for item, preco in PRECO_CUSTO.items() if st.toggle(f"{item} - R$ {preco:,.2f}", key=item)]

with col2:
    st.markdown("### 🛠️ Serviços Adicionais")
    inc_instalacao = st.toggle("Incluir Instalação")
    inc_manutencao = st.toggle("Incluir Manutenção")
    qtd_manutencao = Decimal(st.number_input("Qtd. Manutenções", 1, value=1, step=1)) if inc_manutencao else Decimal("0")
    inc_desinstalacao = st.toggle("Incluir Desinstalação")
    qtd_desinstalacao = Decimal(st.number_input("Qtd. Desinstalações", 1, value=1, step=1)) if inc_desinstalacao else Decimal("0")

# --- Cálculos e Exibição ---
st.markdown("---")
proposta = []
valor_total_locacao = Decimal("0")
mensalidade_venda = Decimal("0")

if itens_selecionados:
    custo_hw = sum(PRECO_CUSTO[item] for item in itens_selecionados)
    mensalidade_custo = (custo_hw / AMORTIZACAO_HARDWARE_MESES).quantize(Decimal("0.01"), ROUND_DOWN)
    mensalidade_venda = (mensalidade_custo * (1 + margem)).quantize(Decimal("0.01"), ROUND_DOWN)
    valor_total_locacao = mensalidade_venda * qtd * contrato
    proposta.append({"Serviço/Produto": "Locação de Equipamentos", "Qtd": f"{int(qtd)} x {int(contrato)} meses", "Valor Unit.": mensalidade_venda, "Total": valor_total_locacao})

valor_total_servicos = Decimal("0")
if inc_instalacao:
    total = c_instalacao * qtd
    proposta.append({"Serviço/Produto": "Taxa de Instalação", "Qtd": int(qtd), "Valor Unit.": c_instalacao, "Total": total})
    valor_total_servicos += total
if inc_manutencao:
    total = c_manutencao * qtd_manutencao
    proposta.append({"Serviço/Produto": "Taxa de Manutenção", "Qtd": int(qtd_manutencao), "Valor Unit.": c_manutencao, "Total": total})
    valor_total_servicos += total
if inc_desinstalacao:
    total = c_desinstalacao * qtd_desinstalacao
    proposta.append({"Serviço/Produto": "Taxa de Desinstalação", "Qtd": int(qtd_desinstalacao), "Valor Unit.": c_desinstalacao, "Total": total})
    valor_total_servicos += total

if proposta:
    valor_global = valor_total_locacao + valor_total_servicos
    st.success("✅ Cálculo da Proposta para Licitação realizado!")
    
    m1, m2 = st.columns(2)
    m1.metric("Mensalidade por Veículo", f"R$ {mensalidade_venda:,.2f}")
    m2.metric("💰 Valor Total do Contrato", f"R$ {valor_global:,.2f}")
    
    st.markdown("### 📊 Detalhamento da Proposta")
    df = pd.DataFrame(proposta)
    st.dataframe(df, use_container_width=True, hide_index=True, column_config={
        "Valor Unit.": st.column_config.NumberColumn("Valor Unit. (R$)", format="R$ %.2f"),
        "Total": st.column_config.NumberColumn("Valor Total (R$)", format="R$ %.2f"),
    })
else:
    st.warning("⚠️ Selecione pelo menos um item ou serviço para calcular a proposta.")
