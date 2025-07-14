# pages/Simulador_Licitação.py
from decimal import Decimal, ROUND_DOWN
import pandas as pd
import streamlit as st

# --- 1. CONFIGURAÇÃO E AUTENTICAÇÃO ---
st.set_page_config(layout="wide", page_title="Simulador Licitações")

if not st.session_state.get("authentication_status"):
    st.error("🔒 Acesso Negado! Por favor, faça login.")
    st.page_link("Simulador_Comercial.py", label="Ir para Login", icon="🏠")
    st.stop()

# --- 2. CONSTANTES ---
PRECO_CUSTO = {
    "Rastreador GPRS/GSM 2G": Decimal("300"), "Rastreador GPRS/GSM 4G": Decimal("400"),
    "Rastreador Satelital": Decimal("900"), "Telemetria/CAN": Decimal("600"),
    "RFID - ID Motorista": Decimal("153"),
}
AMORTIZACAO_HARDWARE_MESES = Decimal("12")

# --- 3. INTERFACE ---
st.markdown("<h1 style='text-align: center; color: #54A033;'>Simulador para Licitações e Editais</h1>", unsafe_allow_html=True)

# Bloco para exibir dados do utilizador logado
st.markdown("---")
col1, col2 = st.columns([1,1])
col1.metric("Utilizador", st.session_state.get('name', 'N/A'))
col2.metric("Nível de Acesso", st.session_state.get('role', 'N/A').capitalize())
st.markdown("---")

st.sidebar.header("📝 Configurações da Licitação")
qtd = Decimal(st.sidebar.number_input("Qtd. de Veículos 🚗", min_value=1, value=1, step=1))
contrato = Decimal(st.sidebar.number_input("Tempo de Contrato (meses) 📆", min_value=12, value=12, step=12))
margem = Decimal(str(st.sidebar.slider("Margem de Lucro (%) 📈", 0, 100, 30))) / 100

st.sidebar.header("🔧 Custos de Serviços (Unitário)")
c_instalacao = Decimal(str(st.sidebar.number_input("Instalação", 0.0, value=50.0, step=10.0, format="%.2f")))
c_manutencao = Decimal(str(st.sidebar.number_input("Manutenção", 0.0, value=50.0, step=10.0, format="%.2f")))
c_desinstalacao = Decimal(str(st.sidebar.number_input("Desinstalação", 0.0, value=50.0, step=10.0, format="%.2f")))

col_a, col_b = st.columns(2)
with col_a:
    st.markdown("### 📦 Itens de Locação")
    itens_selecionados = [item for item, preco in PRECO_CUSTO.items() if st.toggle(f"{item} - R$ {preco:,.2f}", key=item)]

with col_b:
    st.markdown("### 🛠️ Serviços Adicionais")
    inc_instalacao = st.toggle("Incluir Instalação")
    inc_manutencao = st.toggle("Incluir Manutenção")
    qtd_manutencao = Decimal(st.number_input("Qtd. Manutenções", 1, value=1, step=1)) if inc_manutencao else Decimal("0")
    inc_desinstalacao = st.toggle("Incluir Desinstalação")
    qtd_desinstalacao = Decimal(st.number_input("Qtd. Desinstalações", 1, value=1, step=1)) if inc_desinstalacao else Decimal("0")

# --- 4. CÁLCULOS E EXIBIÇÃO ---
st.markdown("---")
proposta = []
valor_total_locacao = Decimal("0")
mensalidade_total_veiculo = Decimal("0")

# ***** CORREÇÃO PRINCIPAL AQUI *****
# Itera sobre cada item selecionado para adicioná-lo como uma linha separada
if itens_selecionados:
    for item in itens_selecionados:
        custo_hw_item = PRECO_CUSTO[item]
        mensalidade_custo_item = (custo_hw_item / AMORTIZACAO_HARDWARE_MESES).quantize(Decimal("0.01"), ROUND_DOWN)
        mensalidade_venda_item = (mensalidade_custo_item * (1 + margem)).quantize(Decimal("0.01"), ROUND_DOWN)
        
        mensalidade_total_veiculo += mensalidade_venda_item # Soma para o total mensal por veículo
        
        proposta.append({
            "Serviço/Produto": f"Locação - {item}",
            "Qtd": f"{int(qtd)} x {int(contrato)} meses",
            "Valor Unit. Mensal": mensalidade_venda_item,
            "Total": mensalidade_venda_item * qtd * contrato
        })
    valor_total_locacao = mensalidade_total_veiculo * qtd * contrato

valor_total_servicos = Decimal("0")
if inc_instalacao:
    total = c_instalacao * qtd
    proposta.append({"Serviço/Produto": "Taxa de Instalação", "Qtd": int(qtd), "Valor Unit. Mensal": c_instalacao, "Total": total})
    valor_total_servicos += total
if inc_manutencao and qtd_manutencao > 0:
    total = c_manutencao * qtd_manutencao
    proposta.append({"Serviço/Produto": "Taxa de Manutenção", "Qtd": int(qtd_manutencao), "Valor Unit. Mensal": c_manutencao, "Total": total})
    valor_total_servicos += total
if inc_desinstalacao and qtd_desinstalacao > 0:
    total = c_desinstalacao * qtd_desinstalacao
    proposta.append({"Serviço/Produto": "Taxa de Desinstalação", "Qtd": int(qtd_desinstalacao), "Valor Unit. Mensal": c_desinstalacao, "Total": total})
    valor_total_servicos += total

if proposta:
    valor_global = valor_total_locacao + valor_total_servicos
    st.success("✅ Cálculo da Proposta para Licitação realizado!")
    
    m1, m2 = st.columns(2)
    m1.metric("Mensalidade por Veículo (Locação)", f"R$ {mensalidade_total_veiculo:,.2f}")
    m2.metric("💰 Valor Total Estimado do Contrato", f"R$ {valor_global:,.2f}")
    
    st.markdown("### 📊 Detalhamento da Proposta")
    df = pd.DataFrame(proposta)
    st.dataframe(df, use_container_width=True, hide_index=True, column_config={
        "Valor Unit. Mensal": st.column_config.NumberColumn("Valor Unitário (R$)", format="R$ %.2f"),
        "Total": st.column_config.NumberColumn("Valor Total (R$)", format="R$ %.2f"),
    })
else:
    st.warning("⚠️ Selecione pelo menos um item ou serviço para calcular a proposta.")
