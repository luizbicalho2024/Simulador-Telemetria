# pages/1_Simulador_PJ.py
from io import BytesIO
from datetime import datetime
from decimal import Decimal
import streamlit as st
import docx # Usando a biblioteca python-docx

# --- 1. CONFIGURAÇÃO DA PÁGINA E VERIFICAÇÃO DE AUTENTICAÇÃO ---
st.set_page_config(layout="wide", page_title="Simulador Pessoa Jurídica")

if not st.session_state.get("authentication_status"):
    st.error("🔒 Acesso Negado! Por favor, faça login na página principal para continuar.")
    st.page_link("Simulador_Comercial.py", label="Ir para Login", icon="🏠")
    st.stop()

if 'proposal_buffer' not in st.session_state:
    st.session_state.proposal_buffer = None
if 'proposal_filename' not in st.session_state:
    st.session_state.proposal_filename = ""

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
    """Gera uma proposta DOCX preenchida usando python-docx."""
    try:
        template_path = "Proposta Comercial e Intenção - Verdio.docx"
        doc = docx.Document(template_path)

        # 1. Substitui os placeholders de texto simples em todo o documento
        placeholders = {
            '{{NOME_EMPRESA}}': context.get('NOME_EMPRESA', ''),
            '{{NOME_RESPONSAVEL}}': context.get('NOME_RESPONSAVEL', ''),
            '{{NOME_CONSULTOR}}': context.get('NOME_CONSULTOR', ''),
            '{{DATA_VALIDADE}}': context.get('DATA_VALIDADE', ''),
            '{{QTD_VEICULOS}}': context.get('QTD_VEICULOS', ''),
            '{{TEMPO_CONTRATO}}': context.get('TEMPO_CONTRATO', ''),
            '{{VALOR_MENSAL_FROTA}}': context.get('VALOR_MENSAL_FROTA', ''),
            '{{VALOR_TOTAL_CONTRATO}}': context.get('VALOR_TOTAL_CONTRATO', ''),
            '{{SOMA_TOTAL_MENSAL_VEICULO}}': context.get('SOMA_TOTAL_MENSAL_VEICULO', '')
        }

        for p in doc.paragraphs:
            for key, value in placeholders.items():
                if key in p.text:
                    # Usa .runs para preservar a formatação
                    inline = p.runs
                    for i in range(len(inline)):
                        if key in inline[i].text:
                            text = inline[i].text.replace(key, value)
                            inline[i].text = text

        # 2. Encontra a tabela de produtos (assumindo que é a primeira tabela do doc)
        # Se houver outras tabelas antes, pode ser necessário ajustar o índice, ex: doc.tables[1]
        tabela_produtos = doc.tables[0]

        # 3. Adiciona os produtos selecionados à tabela
        for item in context.get('itens_proposta', []):
            cells = tabela_produtos.add_row().cells
            cells[0].text = item.get('nome', '')
            cells[1].text = item.get('desc', '')
            cells[2].text = item.get('preco', '')
        
        # 4. Adiciona a linha de total
        total_cells = tabela_produtos.add_row().cells
        total_cells[0].text = "Total Mensal por Veículo"
        total_cells[2].text = context.get('SOMA_TOTAL_MENSAL_VEICULO', '')
        
        # Salva o documento em memória
        buffer = BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        return buffer
    except Exception as e:
        st.error(f"Erro ao gerar o template DOCX: {e}")
        st.info(f"Verifique se o ficheiro '{template_path}' existe e se os placeholders (ex: {{NOME_EMPRESA}}) estão corretos.")
        return None


# --- 4. INTERFACE PRINCIPAL ---
st.markdown("<h1 style='text-align: center; color: #54A033;'>Simulador de Venda - Pessoa Jurídica</h1>", unsafe_allow_html=True)
st.markdown("---")
st.write(f"Usuário: {st.session_state.get('name', 'N/A')} ({st.session_state.get('username', 'N/A')})")
st.write(f"Nível de Acesso: {st.session_state.get('role', 'Indefinido').capitalize()}")
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
    with st.form("form_proposta_pj", clear_on_submit=True):
        empresa = st.text_input("Nome da Empresa")
        responsavel = st.text_input("Nome do Responsável")
        consultor = st.text_input("Nome do Consultor", value=st.session_state.get('name', ''))
        validade = st.date_input("Validade da Proposta", value=datetime.today())
        
        if st.form_submit_button("Gerar Proposta em DOCX"):
            if not all([empresa, responsavel, consultor]):
                st.warning("Preencha todos os campos do formulário.")
            else:
                context = {
                    'NOME_EMPRESA': empresa, 'NOME_RESPONSAVEL': responsavel, 'NOME_CONSULTOR': consultor,
                    'DATA_VALIDADE': validade.strftime("%d/%m/%Y"), 'QTD_VEICULOS': str(qtd_veiculos),
                    'TEMPO_CONTRATO': tempo_contrato, 'VALOR_MENSAL_FROTA': f"R$ {valor_mensal_frota:,.2f}",
                    'VALOR_TOTAL_CONTRATO': f"R$ {valor_total_contrato:,.2f}",
                    'itens_proposta': [{'nome': k, 'desc': PRODUTOS_DESCRICAO.get(k, ''), 'preco': f"R$ {v:,.2f}"} for k, v in produtos_selecionados.items()],
                    'SOMA_TOTAL_MENSAL_VEICULO': f"R$ {soma_mensal_veiculo:,.2f}"
                }
                
                st.session_state.proposal_buffer = gerar_proposta_docx(context)
                st.session_state.proposal_filename = f"Proposta_{empresa.replace(' ', '_')}.docx"
    
    if st.session_state.proposal_buffer is not None:
        st.download_button(
            label="📥 Baixar Proposta Gerada",
            data=st.session_state.proposal_buffer,
            file_name=st.session_state.proposal_filename,
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        if st.button("Limpar Proposta Gerada"):
            st.session_state.proposal_buffer = None
            st.rerun()

else:
    st.info("Selecione produtos para ver o cálculo e gerar a proposta.")
