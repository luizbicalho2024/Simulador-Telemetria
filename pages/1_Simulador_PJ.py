# pages/1_Simulador_PJ.py
from io import BytesIO
from datetime import datetime
from decimal import Decimal # <-- LINHA ADICIONADA PARA CORRIGIR O ERRO
import streamlit as st
from docxtpl import DocxTemplate
import user_management_db as umdb

# --- 1. CONFIGURAÇÃO E AUTENTICAÇÃO ---
st.set_page_config(layout="wide", page_title="Simulador Pessoa Jurídica", page_icon="imgs/v-c.png")

if not st.session_state.get("authentication_status"):
    st.error("🔒 Acesso Negado! Por favor, faça login para visualizar esta página.")
    st.stop()

# --- 2. CARREGAMENTO DE PREÇOS E ESTADO ---
pricing_config = umdb.get_pricing_config()
PLANOS_PJ = {k: {p: Decimal(str(v)) for p, v in val.items()} for k, v in pricing_config.get("PLANOS_PJ", {}).items()}
PRODUTOS_PJ_DESCRICAO = pricing_config.get("PRODUTOS_PJ_DESCRICAO", {})

if 'pj_results' not in st.session_state:
    st.session_state.pj_results = {}

# --- 3. FUNÇÃO AUXILIAR PARA GERAR O DOCX ---
@st.cache_data
def gerar_proposta_docx(context):
    """Gera uma proposta DOCX preenchida usando docxtpl e retorna um buffer de memória."""
    try:
        doc = DocxTemplate("Proposta Comercial e Intenção - Verdio.docx")
        doc.render(context)
        buffer = io.BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        return buffer
    except Exception as e:
        st.error(f"Erro ao gerar o template DOCX: {e}")
        st.info("Verifique se o ficheiro 'Proposta Comercial e Intenção - Verdio.docx' está na pasta raiz e se os placeholders estão corretos.")
        return None

# --- 4. INTERFACE ---
st.sidebar.image("imgs/v-c.png", width=120)
if st.sidebar.button("🧹 Limpar Campos e Simulação", use_container_width=True, key="pj_clear"):
    keys_to_clear = [k for k in st.session_state if k.startswith("pj_")]
    for k in keys_to_clear:
        del st.session_state[k]
    st.session_state.pj_results = {}
    st.toast("Campos limpos!", icon="✨")
    st.rerun()

try:
    st.image("imgs/logo.png", width=250)
except: pass

st.markdown("<h1 style='text-align: center; color: #54A033;'>Simulador de Venda - Pessoa Jurídica</h1>", unsafe_allow_html=True)
st.write(f"Usuário: {st.session_state.get('name', 'N/A')} ({st.session_state.get('username', 'N/A')})")
st.write(f"Nível de Acesso: {st.session_state.get('role', 'Indefinido').capitalize()}")
st.markdown("---")

# --- 5. FORMULÁRIO DE SIMULAÇÃO ---
with st.form("form_simulacao_pj"):
    st.sidebar.header("📝 Configurações PJ")
    qtd_veiculos = st.sidebar.number_input("Quantidade de Veículos 🚗", min_value=1, value=1, step=1, key="pj_qtd")
    tempo_contrato = st.sidebar.selectbox("Tempo de Contrato ⏳", list(PLANOS_PJ.keys()), key="pj_contrato")
    
    st.subheader("📄 Informações da Proposta")
    empresa = st.text_input("Nome da Empresa", key="pj_empresa")
    responsavel = st.text_input("Nome do Responsável", key="pj_responsavel")
    
    st.markdown("### 🛠️ Selecione os Produtos:")
    produtos_selecionados = {}
    col_a, col_b = st.columns(2)
    for i, (produto, preco) in enumerate(PLANOS_PJ.get(tempo_contrato, {}).items()):
        target_col = col_a if i % 2 == 0 else col_b
        if target_col.toggle(f"{produto} - R$ {preco:,.2f}", key=f"pj_toggle_{produto.replace(' ', '_')}"):
            produtos_selecionados[produto] = preco

    submitted = st.form_submit_button("Simular e Registrar Proposta")

    if submitted:
        if not all([empresa, responsavel]):
            st.warning("Preencha o Nome da Empresa e do Responsável.")
        elif not produtos_selecionados:
            st.warning("Selecione pelo menos um produto para simular.")
        else:
            soma_mensal_veiculo = sum(produtos_selecionados.values())
            valor_mensal_frota = soma_mensal_veiculo * Decimal(qtd_veiculos)
            meses_contrato = int(tempo_contrato.split()[0])
            valor_total_contrato = valor_mensal_frota * Decimal(meses_contrato)
            
            st.session_state.pj_results = {
                'soma_mensal_veiculo': soma_mensal_veiculo,
                'valor_mensal_frota': valor_mensal_frota,
                'valor_total_contrato': valor_total_contrato,
                'context': {
                    'NOME_EMPRESA': empresa, 'NOME_RESPONSAVEL': responsavel, 
                    'NOME_CONSULTOR': st.session_state.get('name', ''), 'DATA_VALIDADE': datetime.today().strftime("%d/%m/%Y"),
                    'QTD_VEICULOS': str(qtd_veiculos), 'TEMPO_CONTRATO': tempo_contrato, 
                    'VALOR_MENSAL_FROTA': f"R$ {valor_mensal_frota:,.2f}", 'VALOR_TOTAL_CONTRATO': f"R$ {valor_total_contrato:,.2f}",
                    'itens_proposta': [{'nome': k, 'desc': PRODUTOS_PJ_DESCRICAO.get(k, ''), 'preco': f"R$ {v:,.2f}"} for k, v in produtos_selecionados.items()],
                    'SOMA_TOTAL_MENSAL_VEICULO': f"R$ {soma_mensal_veiculo:,.2f}"
                }
            }
            
            proposal_log_data = {"tipo": "PJ", "empresa": empresa, "consultor": st.session_state.get('name', 'N/A'), "valor_total": float(valor_total_contrato)}
            umdb.upsert_proposal(proposal_log_data)
            umdb.add_log(st.session_state["username"], "Simulou/Registrou Proposta PJ", details={"empresa": empresa, "valor": f"R$ {valor_total_contrato:,.2f}"})

# --- 6. EXIBIÇÃO DOS RESULTADOS E DOWNLOAD ---
if st.session_state.pj_results:
    res = st.session_state.pj_results
    st.markdown("---")
    st.subheader("Resultados da Simulação")
    st.success(f"**Valor Mensal por Veículo:** R$ {res['soma_mensal_veiculo']:,.2f}")
    st.info(f"**Valor Mensal Total (Frota):** R$ {res['valor_mensal_frota']:,.2f}")
    st.info(f"**Valor Total do Contrato:** R$ {res['valor_total_contrato']:,.2f}")

    docx_buffer = gerar_proposta_docx(res['context'])
    if docx_buffer:
        st.download_button(
            label="📥 Baixar Proposta (.docx)", data=docx_buffer,
            file_name=f"Proposta_{res['context']['NOME_EMPRESA'].replace(' ', '_')}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
