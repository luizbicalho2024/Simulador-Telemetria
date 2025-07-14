# pages/Simulador_PJ.py
from io import BytesIO
from datetime import datetime
from decimal import Decimal
import streamlit as st
from docxtpl import DocxTemplate

# --- 1. CONFIGURAÇÃO DA PÁGINA E VERIFICAÇÃO DE AUTENTICAÇÃO ---
st.set_page_config(layout="wide", page_title="Simulador Pessoa Jurídica")

if not st.session_state.get("authentication_status"):
    st.error("🔒 Acesso Negado! Por favor, faça login na página principal para continuar.")
    st.page_link("Simulador_Comercial.py", label="Ir para Login", icon="🏠")
    st.stop()

# --- 2. CONSTANTES E DADOS ---
PLANOS = {
    "12 Meses": {"GPRS / Gsm": Decimal("80.88"), "Satélite": Decimal("193.80"), "Identificador de Motorista / RFID": Decimal("19.25"), "Leitor de Rede CAN / Telemetria": Decimal("75.25"), "Videomonitoramento + DMS + ADAS": Decimal("409.11")},
    "24 Meses": {"GPRS / Gsm": Decimal("53.92"), "Satélite": Decimal("129.20"), "Identificador de Motorista / RFID": Decimal("12.83"), "Leitor de Rede CAN / Telemetria": Decimal("50.17"), "Videomonitoramento + DMS + ADAS": Decimal("272.74")},
    "36 Meses": {"GPRS / Gsm": Decimal("44.93"), "Satélite": Decimal("107.67"), "Identificador de Motorista / RFID": Decimal("10.69"), "Leitor de Rede CAN / Telemetria": Decimal("41.81"), "Videomonitoramento + DMS + ADAS": Decimal("227.28")}
}
PRODUTOS_DESCRICAO = {
    "GPRS / Gsm": "Equipamento de rastreamento GSM/GPRS 2G ou 4G.", "Satélite": "Equipamento de rastreamento via satélite para cobertura total.",
    "Identificador de Motorista / RFID": "Identificação automática de motoristas via RFID.", "Leitor de Rede CAN / Telemetria": "Leitura de dados avançados de telemetria via rede CAN do veículo.",
    "Videomonitoramento + DMS + ADAS": "Sistema de videomonitoramento com câmeras, alertas de fadiga (DMS) e assistência ao motorista (ADAS)."
}

# --- 3. FUNÇÃO AUXILIAR PARA GERAR O DOCX ---
def gerar_proposta_docx(context):
    """Gera uma proposta DOCX preenchida usando docxtpl e retorna um buffer de memória."""
    try:
        # Garante que o template é lido corretamente
        doc = DocxTemplate("Proposta Comercial e Intenção - Verdio.docx")
        doc.render(context)
        
        buffer = BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        return buffer
    except Exception as e:
        st.error(f"Erro ao gerar o template DOCX: {e}")
        st.info("Verifique se o ficheiro 'Proposta Comercial e Intenção - Verdio.docx' está na pasta raiz e se os placeholders (ex: {{ NOME_EMPRESA }}) estão corretos.")
        return None

# --- 4. INTERFACE PRINCIPAL ---
st.markdown("<h1 style='text-align: center; color: #54A033;'>Simulador de Venda - Pessoa Jurídica</h1>", unsafe_allow_html=True)

# Bloco para exibir dados do utilizador logado
st.markdown("---")
col1, col2 = st.columns([1,1])
col1.metric("Utilizador", st.session_state.get('name', 'N/A'))
col2.metric("Nível de Acesso", st.session_state.get('role', 'N/A').capitalize())
st.markdown("---")

st.sidebar.header("📝 Configurações PJ")
qtd_veiculos = st.sidebar.number_input("Quantidade de Veículos 🚗", min_value=1, value=1, step=1)
tempo_contrato = st.sidebar.selectbox("Tempo de Contrato ⏳", list(PLANOS.keys()))

st.markdown("### 🛠️ Selecione os Produtos:")
produtos_selecionados = {}
col_a, col_b = st.columns(2)
for i, (produto, preco) in enumerate(PLANOS[tempo_contrato].items()):
    target_col = col_a if i % 2 == 0 else col_b
    if target_col.toggle(f"{produto} - R$ {preco:,.2f}", key=f"pj_toggle_{i}"):
        produtos_selecionados[produto] = preco

# --- 5. CÁLCULOS E FORMULÁRIO DE GERAÇÃO ---
if produtos_selecionados:
    soma_mensal_veiculo = sum(produtos_selecionados.values())
    valor_mensal_frota = soma_mensal_veiculo * qtd_veiculos
    meses_contrato = int(tempo_contrato.split()[0])
    valor_total_contrato = valor_mensal_frota * meses_contrato

    st.markdown("---")
    st.success(f"**Valor Mensal por Veículo:** R$ {soma_mensal_veiculo:,.2f}")
    st.info(f"**Valor Mensal Total (Frota):** R$ {valor_mensal_frota:,.2f}")
    st.info(f"**Valor Total do Contrato:** R$ {valor_total_contrato:,.2f}")
    
    st.markdown("---")
    st.subheader("📄 Gerar Proposta")
    with st.form("form_proposta_pj", clear_on_submit=False):
        empresa = st.text_input("Nome da Empresa")
        responsavel = st.text_input("Nome do Responsável")
        consultor = st.text_input("Nome do Consultor", value=st.session_state.get('name', ''))
        validade = st.date_input("Validade da Proposta", value=datetime.today())
        
        if st.form_submit_button("Gerar Proposta em DOCX"):
            if not all([empresa, responsavel, consultor]):
                st.warning("Preencha todos os campos do formulário.")
            else:
                # Contexto com os dados para o template
                context = {
                    'NOME_EMPRESA': empresa, 'NOME_RESPONSAVEL': responsavel, 'NOME_CONSULTOR': consultor,
                    'DATA_VALIDADE': validade.strftime("%d/%m/%Y"), 'QTD_VEICULOS': str(qtd_veiculos),
                    'TEMPO_CONTRATO': tempo_contrato, 'VALOR_MENSAL_FROTA': f"R$ {valor_mensal_frota:,.2f}",
                    'VALOR_TOTAL_CONTRATO': f"R$ {valor_total_contrato:,.2f}",
                    'itens_proposta': [{'nome': k, 'desc': PRODUTOS_DESCRICAO.get(k, ''), 'preco': f"R$ {v:,.2f}"} for k, v in produtos_selecionados.items()],
                    'SOMA_TOTAL_MENSAL_VEICULO': f"R$ {soma_mensal_veiculo:,.2f}"
                }
                
                doc_buffer = gerar_proposta_docx(context)
                if doc_buffer:
                    st.download_button(
                        label="📥 Baixar Proposta em DOCX", data=doc_buffer,
                        file_name=f"Proposta_{empresa.replace(' ', '_')}.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    )
else:
    st.info("Selecione produtos para ver o cálculo e gerar a proposta.")
