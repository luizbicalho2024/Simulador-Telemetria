# pages/2_Simulador_PF.py
from decimal import Decimal, ROUND_DOWN
import streamlit as st
import user_management_db as umdb

st.set_page_config(layout="wide", page_title="Simulador Pessoa Física", page_icon="imgs/v-c.png")
if not st.session_state.get("authentication_status"):
    st.error("🔒 Acesso Negado!"); st.stop()

# --- 1. CARREGAMENTO DE PREÇOS E ESTADO ---
pricing_config = umdb.get_pricing_config()
PRECOS_PF = {k: Decimal(str(v)) for k, v in pricing_config.get("PRECOS_PF", {}).items()}
TAXAS_PARCELAMENTO_PF = {str(k): Decimal(str(v)) for k, v in pricing_config.get("TAXAS_PARCELAMENTO_PF", {}).items()}

if 'pf_results' not in st.session_state:
    st.session_state.pf_results = {}

# --- 2. INTERFACE ---
st.sidebar.image("imgs/v-c.png", width=120)
if st.sidebar.button("🧹 Limpar Campos", use_container_width=True, key="pf_clear"):
    keys_to_clear = [k for k in st.session_state if k.startswith("pf_")]
    for k in keys_to_clear: del st.session_state[k]
    st.session_state.pf_results = {}
    st.toast("Campos limpos!", icon="✨"); st.rerun()

try:
    st.image("imgs/logo.png", width=250)
except: pass

st.markdown("<h1 style='text-align: center; color: #54A033;'>Simulador de Venda - Pessoa Física</h1>", unsafe_allow_html=True)
st.markdown("---")
st.write(f"Usuário: {st.session_state.get('name', 'N/A')} ({st.session_state.get('username', 'N/A')})")
st.write(f"Nível de Acesso: {st.session_state.get('role', 'Indefinido').capitalize()}")
st.markdown("---")

# --- 3. CONFIGURAÇÕES INTERATIVAS (FORA DO FORMULÁRIO) ---
st.sidebar.header("📝 Configurações PF")
modelo = st.sidebar.selectbox("Tipo de Rastreador 📡", list(PRECOS_PF.keys()), key="pf_modelo")
preco_base = PRECOS_PF.get(modelo, Decimal("0"))
st.markdown(f"#### Valor Anual à Vista (Base): R$ {preco_base:,.2f}")

st.markdown("#### Opções de Pagamento")

# Desconto
col1, col2 = st.columns([1, 3])
desconto_ativo = col1.checkbox("Aplicar Desconto", key="pf_desconto_check")
if desconto_ativo:
    percent_desconto = col2.number_input("Percentual de Desconto (%)", min_value=0.0, max_value=100.0, step=1.0, format="%.2f", key="pf_desconto_percent")
else:
    percent_desconto = 0.0

# Parcelamento
parcelamento_ativo = st.checkbox("Ativar Parcelamento", key="pf_parcela_check")
if parcelamento_ativo:
    num_parcelas_str = st.selectbox("Quantidade de Parcelas:", list(TAXAS_PARCELAMENTO_PF.keys()), key="pf_num_parcelas")
else:
    num_parcelas_str = "0"


# --- 4. FORMULÁRIO PARA AÇÃO FINAL ---
with st.form("form_simulacao_pf"):
    st.subheader("Informações do Cliente")
    nome_cliente = st.text_input("Nome do Cliente", key="pf_nome_cliente")
    
    submitted = st.form_submit_button("Simular e Registrar")

    if submitted:
        if not nome_cliente:
            st.warning("Por favor, insira o nome do cliente.")
        else:
            preco_final = preco_base
            if desconto_ativo and percent_desconto > 0:
                desconto = (preco_base * (Decimal(str(percent_desconto)) / 100)).quantize(Decimal('0.01'), ROUND_DOWN)
                preco_final = preco_base - desconto
            
            valor_proposta = preco_final
            
            resultados = {
                "preco_final": preco_final,
                "parcelamento_ativo": parcelamento_ativo,
                "valor_proposta": valor_proposta
            }
            
            if parcelamento_ativo:
                taxa_juros = TAXAS_PARCELAMENTO_PF.get(num_parcelas_str, Decimal("0"))
                num_parcelas = int(num_parcelas_str)
                valor_com_juros = preco_final * (Decimal(1) + taxa_juros)
                valor_parcela = (valor_com_juros / Decimal(num_parcelas)).quantize(Decimal('0.01'), ROUND_DOWN)
                total_parcelado = valor_parcela * Decimal(num_parcelas)
                valor_proposta = total_parcelado
                
                resultados.update({
                    "num_parcelas": num_parcelas,
                    "valor_parcela": valor_parcela,
                    "total_parcelado": total_parcelado,
                    "valor_proposta": valor_proposta
                })

            st.session_state.pf_results = resultados
            
            umdb.add_log(st.session_state["username"], "Simulou/Registrou Proposta PF", f"Cliente: {nome_cliente}, Valor: R$ {valor_proposta:,.2f}")
            umdb.log_proposal({"tipo": "PF", "empresa": nome_cliente, "consultor": st.session_state.get('name', 'N/A'), "valor_total": float(valor_proposta)})
            st.toast("Proposta registrada no dashboard!", icon="📊")

# --- 5. EXIBIÇÃO DOS RESULTADOS ---
if st.session_state.pf_results:
    res = st.session_state.pf_results
    st.markdown("---")
    st.subheader("Resultados da Simulação")
    st.info(f"**Valor Final (com desconto):** R$ {res['preco_final']:,.2f}")
    
    if res["parcelamento_ativo"]:
        st.success(f"**Parcelado em {res['num_parcelas']}x de R$ {res['valor_parcela']:,.2f}**")
        st.markdown(f"##### Valor Total Parcelado: R$ {res['total_parcelado']:,.2f}")
