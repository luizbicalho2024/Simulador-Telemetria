# pages/1_Simulador_PJ.py
from io import BytesIO
from datetime import datetime
from decimal import Decimal
import streamlit as st
from docxtpl import DocxTemplate
import user_management_db as umdb

# --- 1. CONFIGURAÇÃO E AUTENTICAÇÃO ---
st.set_page_config(layout="wide", page_title="Simulador Pessoa Jurídica", page_icon="imgs/v-c.png")

if not st.session_state.get("authentication_status"):
    st.error("🔒 Acesso Negado!"); st.stop()

# --- 2. CARREGAMENTO DE PREÇOS E ESTADO ---
pricing_config = umdb.get_pricing_config()
PLANOS_PJ = {k: {p: Decimal(str(v)) for p, v in val.items()} for k, val in pricing_config.get("PLANOS_PJ", {}).items()}
PRODUTOS_PJ_DESCRICAO = pricing_config.get("PRODUTOS_PJ_DESCRICAO", {})

# Inicializa o estado da página
if 'pj_proposal_registered' not in st.session_state:
    st.session_state.pj_proposal_registered = False
if 'pj_context' not in st.session_state:
    st.session_state.pj_context = None

# --- 3. FUNÇÃO AUXILIAR PARA GERAR O DOCX ---
def gerar_proposta_docx(context):
    try:
        template_path = "Proposta Comercial e Intenção - Verdio.docx"
        doc = DocxTemplate(template_path)
        doc.render(context)
        buffer = BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        return buffer
    except Exception as e:
        st.error(f"Erro ao gerar o template DOCX: {e}")
        return None

# --- 4. INTERFACE ---
st.sidebar.image("imgs/v-c.png", width=120)
if st.sidebar.button("🧹 Limpar Campos e Proposta", use_container_width=True, key="pj_clear"):
    keys_to_clear = [k for k in st.session_state if k.startswith("pj_")]
    for k in keys_to_clear: del st.session_state[k]
    st.toast("Campos limpos!", icon="✨"); st.rerun()

try:
    st.image("imgs/logo.png", width=250)
except: pass

st.markdown("<h1 style='text-align: center; color: #54A033;'>Simulador de Venda - Pessoa Jurídica</h1>", unsafe_allow_html=True)
st.markdown("---")
st.write(f"Usuário: {st.session_state.get('name', 'N/A')} ({st.session_state.get('username', 'N/A')})")
st.write(f"Nível de Acesso: {st.session_state.get('role', 'Indefinido').capitalize()}")
st.markdown("---")

st.sidebar.header("📝 Configurações PJ")
qtd_veiculos = st.sidebar.number_input("Quantidade de Veículos 🚗", min_value=1, value=1, step=1, key="pj_qtd")
tempo_contrato = st.sidebar.selectbox("Tempo de Contrato ⏳", list(PLANOS_PJ.keys()), key="pj_contrato")

st.markdown("### 🛠️ Selecione os Produtos:")
produtos_selecionados = {}
col_a, col_b = st.columns(2)
for i, (produto, preco) in enumerate(PLANOS_PJ.get(tempo_contrato, {}).items()):
    target_col = col_a if i % 2 == 0 else col_b
    if target_col.toggle(f"{produto} - R$ {preco:,.2f}", key=f"pj_toggle_{produto.replace(' ', '_')}"):
        produtos_selecionados[produto] = preco

# --- 5. CÁLCULOS E GERAÇÃO ---
if produtos_selecionados:
    soma_mensal_veiculo = sum(produtos_selecionados.values())
    valor_mensal_frota = soma_mensal_veiculo * Decimal(qtd_veiculos)
    meses_contrato = int(tempo_contrato.split()[0])
    valor_total_contrato = valor_mensal_frota * Decimal(meses_contrato)

    st.markdown("---")
    st.success(f"**Valor Mensal por Veículo:** R$ {soma_mensal_veiculo:,.2f}")
    st.info(f"**Valor Mensal Total (Frota):** R$ {valor_mensal_frota:,.2f}")
    st.info(f"**Valor Total do Contrato:** R$ {valor_total_contrato:,.2f}")
    
    st.markdown("---")
    st.subheader("📄 Etapa 1: Registrar Proposta")
    with st.form("form_registrar_proposta_pj"):
        empresa = st.text_input("Nome da Empresa", key="pj_empresa")
        responsavel = st.text_input("Nome do Responsável", key="pj_responsavel")
        consultor = st.text_input("Nome do Consultor", value=st.session_state.get('name', ''), key="pj_consultor")
        validade = st.date_input("Validade da Proposta", value=datetime.today(), key="pj_validade")
        
        if st.form_submit_button("Registrar Proposta no Dashboard"):
            if all([empresa, responsavel, consultor]):
                st.session_state.pj_context = {
                    'NOME_EMPRESA': empresa, 'NOME_RESPONSAVEL': responsavel, 'NOME_CONSULTOR': consultor,
                    'DATA_VALIDADE': validade.strftime("%d/%m/%Y"), 'QTD_VEICULOS': str(qtd_veiculos),
                    'TEMPO_CONTRATO': tempo_contrato, 'VALOR_MENSAL_FROTA': f"R$ {valor_mensal_frota:,.2f}",
                    'VALOR_TOTAL_CONTRATO': f"R$ {valor_total_contrato:,.2f}",
                    'itens_proposta': [{'nome': k, 'desc': PRODUTOS_PJ_DESCRICAO.get(k, ''), 'preco': f"R$ {v:,.2f}"} for k, v in produtos_selecionados.items()],
                    'SOMA_TOTAL_MENSAL_VEICULO': f"R$ {soma_mensal_veiculo:,.2f}"
                }
                
                umdb.add_log(st.session_state["username"], "Registrou Proposta PJ", f"Empresa: {empresa}, Valor: R$ {valor_total_contrato:,.2f}")
                umdb.log_proposal({"tipo": "PJ", "empresa": empresa, "consultor": st.session_state.get('name', 'N/A'), "valor_total": float(valor_total_contrato)})
                
                st.session_state.pj_proposal_registered = True
                st.toast("Proposta registrada com sucesso! Agora você pode gerar o documento.", icon="✅")
            else:
                st.warning("Preencha todos os campos do formulário.")

    if st.session_state.pj_proposal_registered:
        st.markdown("---")
        st.subheader("📄 Etapa 2: Gerar Documento")
        
        # Gera o buffer do DOCX para o download
        docx_buffer = gerar_proposta_docx(st.session_state.pj_context)
        
        if docx_buffer:
            st.download_button(
                label="📥 Baixar Proposta Gerada (.docx)",
                data=docx_buffer,
                file_name=f"Proposta_{st.session_state.pj_context['NOME_EMPRESA'].replace(' ', '_')}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
