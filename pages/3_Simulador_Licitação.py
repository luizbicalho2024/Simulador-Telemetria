# pages/3_Simulador_Licitação.py
from decimal import Decimal, ROUND_DOWN, ROUND_HALF_UP
import pandas as pd
import streamlit as st
import user_management_db as umdb

# --- 1. CONFIGURAÇÃO E AUTENTICAÇÃO ---
st.set_page_config(
    layout="wide",
    page_title="Simulador Licitações",
    page_icon="imgs/v-c.png"
)

if not st.session_state.get("authentication_status"):
    st.error("🔒 Acesso Negado! Por favor, faça login.")
    st.stop()

# --- 2. CARREGAMENTO DE PREÇOS DINÂMICOS ---
pricing_config = umdb.get_pricing_config()
PRECO_CUSTO = {k: Decimal(str(v)) for k, v in pricing_config.get("PRECO_CUSTO_LICITACAO", {}).items()}
AMORTIZACAO_HARDWARE_MESES = Decimal(str(pricing_config.get("AMORTIZACAO_HARDWARE_MESES", 12)))

# --- 3. INTERFACE ---
st.sidebar.image("imgs/v-c.png", width=120)
if st.sidebar.button("🧹 Limpar Campos", use_container_width=True, key="licit_clear"):
    keys_to_clear = [k for k in st.session_state if k.startswith("licit_")]
    for k in keys_to_clear:
        del st.session_state[k]
    st.toast("Campos limpos!", icon="✨")
    st.rerun()

try:
    st.image("imgs/logo.png", width=250)
except:
    pass

st.markdown("<h1 style='text-align: center; color: #54A033;'>Simulador para Licitações e Editais</h1>", unsafe_allow_html=True)
st.markdown("---")
st.write(f"Usuário: {st.session_state.get('name', 'N/A')} ({st.session_state.get('username', 'N/A')})")
st.write(f"Nível de Acesso: {st.session_state.get('role', 'Indefinido').capitalize()}")
st.markdown("---")

st.sidebar.header("📝 Configurações da Licitação")
qtd = Decimal(st.sidebar.number_input("Qtd. de Veículos 🚗", min_value=1, value=1, step=1, key="licit_qtd"))
contrato = Decimal(st.sidebar.number_input("Tempo de Contrato (meses) 📆", min_value=12, value=12, step=12, key="licit_contrato"))
margem = Decimal(str(st.sidebar.slider("Margem de Lucro (%) 📈", 0, 100, 30, key="licit_margem"))) / 100

st.sidebar.header("🔧 Custos de Serviços (Unitário)")
c_instalacao = Decimal(str(st.sidebar.number_input("Instalação", 0.0, value=50.0, step=10.0, format="%.2f", key="licit_c_inst")))
c_manutencao = Decimal(str(st.sidebar.number_input("Manutenção", 0.0, value=50.0, step=10.0, format="%.2f", key="licit_c_man")))
c_desinstalacao = Decimal(str(st.sidebar.number_input("Desinstalação", 0.0, value=50.0, step=10.0, format="%.2f", key="licit_c_desinst")))

col_a, col_b = st.columns(2)
with col_a:
    st.markdown("### 📦 Itens de Locação")
    itens_selecionados = [item for item, preco in PRECO_CUSTO.items() if st.toggle(f"{item} - R$ {preco:,.2f}", key=f"licit_item_{item}")]
with col_b:
    st.markdown("### 🛠️ Serviços Adicionais")
    inc_instalacao = st.toggle("Incluir Instalação", key="licit_inc_inst")
    inc_manutencao = st.toggle("Incluir Manutenção", key="licit_inc_man")
    qtd_manutencao = Decimal(st.number_input("Qtd. Manutenções", 1, value=1, step=1, key="licit_qtd_man")) if inc_manutencao else Decimal("0")
    inc_desinstalacao = st.toggle("Incluir Desinstalação", key="licit_inc_desinst")
    qtd_desinstalacao = Decimal(st.number_input("Qtd. Desinstalações", 1, value=1, step=1, key="licit_qtd_desinst")) if inc_desinstalacao else Decimal("0")

# --- 4. CÁLCULOS E EXIBIÇÃO ---
st.markdown("---")
proposta = []
valor_total_locacao = Decimal("0")
mensalidade_total_veiculo = Decimal("0")

if itens_selecionados:
    for item in itens_selecionados:
        custo_hw_item = PRECO_CUSTO.get(item, Decimal("0"))
        mensalidade_custo_item = (custo_hw_item / AMORTIZACAO_HARDWARE_MESES).quantize(Decimal("0.01"), rounding=ROUND_DOWN)
        mensalidade_venda_item = (mensalidade_custo_item * (1 + margem)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        mensalidade_total_veiculo += mensalidade_venda_item
        proposta.append({
            "Serviço/Produto": f"Locação - {item}", "Qtd": f"{int(qtd)} x {int(contrato)} meses",
            "Valor Unit. Mensal": mensalidade_venda_item, "Total": mensalidade_venda_item * qtd * contrato
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
    st.toast("Cálculo da proposta realizado com sucesso!", icon="✅")
    
    m1, m2 = st.columns(2)
    m1.metric("Mensalidade por Veículo (Locação)", f"R$ {mensalidade_total_veiculo:,.2f}")
    m2.metric("💰 Valor Total Estimado do Contrato", f"R$ {valor_global:,.2f}")
    
    st.markdown("### 📊 Detalhamento da Proposta")
    df = pd.DataFrame(proposta)
    soma_valor_unitario = df["Valor Unit. Mensal"].sum()
    total_row = pd.DataFrame([{"Serviço/Produto": "VALOR TOTAL GERAL", "Qtd": "", "Valor Unit. Mensal": soma_valor_unitario, "Total": valor_global}])
    df_final = pd.concat([df, total_row], ignore_index=True)

    def highlight_last_row(row):
        return ['font-weight: bold'] * len(row) if row["Serviço/Produto"] == "VALOR TOTAL GERAL" else [''] * len(row)

    styled_df = df_final.style.apply(highlight_last_row, axis=1)
    
    st.dataframe(styled_df, use_container_width=True, hide_index=True, column_config={
        "Valor Unit. Mensal": st.column_config.NumberColumn("Valor Unitário (R$)", format="R$ %.2f"),
        "Total": st.column_config.NumberColumn("Valor Total (R$)", format="R$ %.2f"),
    })
else:
    st.warning("⚠️ Selecione pelo menos um item ou serviço para calcular a proposta.")
