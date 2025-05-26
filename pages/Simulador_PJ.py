# pages/Simulador_PJ.py
# Importações Python padrão primeiro
from io import BytesIO
from docx import Document 
from docx.shared import Pt
import requests
import time
from datetime import datetime
from decimal import Decimal, ROUND_DOWN 

import streamlit as st

# 1. st.set_page_config() - PRIMEIRO COMANDO STREAMLIT
st.set_page_config(
    layout="wide",
    page_title="Simulador Pessoa Jurídica", 
    page_icon="imgs/v-c.png", # Verifique se o caminho está correto
    initial_sidebar_state="expanded"
)

# 2. BLOCO DE VERIFICAÇÃO DE AUTENTICAÇÃO
auth_status = st.session_state.get("authentication_status", False)
if auth_status is not True:
    st.error("🔒 Acesso Negado! Por favor, faça login na página principal para continuar.")
    print(f"ACCESS_DENIED_LOG (Simulador_PJ.py): User not authenticated. Status: {auth_status}")
    try:
        st.page_link("Simulador_Comercial.py", label="Ir para Login", icon="🏠")
    except AttributeError: 
        st.info("Retorne à página principal para efetuar o login.")
    st.stop() 

current_username = st.session_state.get('username', 'N/A')
current_role = st.session_state.get('role', 'Indefinido') 
current_name = st.session_state.get('name', 'N/A')

print(f"INFO_LOG (Simulador_PJ.py): User '{current_username}' authenticated. Role: '{current_role}'")

# 3. Restante do código da sua página

# Busca a API Key do CloudConvert dos segredos do Streamlit
API_KEY_CLOUDCONVERT = st.secrets.get("eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJhdWQiOiIxIiwianRpIjoiZmNhNjY2Y2E5NzEyMGYzNTgxM2IwNDVkMjA4OTYxODM1NGQxNjU0NjBkZjE1M2QwYzBiZjM4MjA5NGMxZDdjODUxMTg2Mzc1OTUxMDRhZDkiLCJpYXQiOjE3NDU4NzYwNTEuMjUwNjg1LCJuYmYiOjE3NDU4NzYwNTEuMjUwNjg2LCJleHAiOjQ5MDE1NDk2NTEuMjQ0MjU3LCJzdWIiOiI3MTc3MDMzMSIsInNjb3BlcyI6WyJ3ZWJob29rLndyaXRlIiwid2ViaG9vay5yZWFkIiwidGFzay53cml0ZSIsInRhc2sucmVhZCJdfQ.chEPyU6axXxsQTOqAvRg9qzKZP_gOgaKC4OyWuCPZDrwctEW63d-4hRt-4W9FL-aSqTcaXreBn2nax94T4zl_APuZj4bcRJefga8-uOhqWrUX6cAHjumev-BXILmtxi0XbgXkz4wZ-rsVP3-ETCfYq-GPYTnU-va6MgclBtVMOMM6I9-Yh-sCHiYBawPR_zzoHxk6j880I1CVHg42yGHfcIw83gq6Jfle7PrZaScPh3PzBl97STdRUeuaw6pwaTC8CPCTHV3YA3XU3JQd7i1o2t2PerMXuD79dk45NZxvJX8KJCcPtvnNCGFrI677X3nLfo86eUgnqtLbrRO1COhtU5spZUTNWqms2pGLfJFgotRUAc9T3NLHjVWF3841v0MjcIr1dLXFgf0KMbmI0pBmmotFw7t29Juid1pv5evRIRpYSbEvCNrpg9uIXlxPVPM863aZbBvqSalQAsYwkdv0Wvw16Z7cm2dgqHY-Xpv0I8Yubv61OJ4yirZPQNkXVoV-4DIFY-IHkRyX3C7fYwnAWXyK8wnskrDfHm5yegTVPduVmp8RzeH8WMSBmPlDLsU7KXc_4FhR212A5fzlfKhgVqIUlHKzoq-S-kyigNUUrSQt4ugYKX_2kEZKZMs6UMqt7MHTU7mLT1QWZOmMFBSDReHV0QwwLsKkaP4jkMNKoQ") 

if not API_KEY_CLOUDCONVERT:
    print("WARN_LOG (Simulador_PJ.py): CLOUDCONVERT_API_KEY não configurada nos segredos.")
    # O aviso ao usuário será mostrado mais abaixo, condicionalmente.

try:
    st.image("imgs/logo.png", width=250) 
except FileNotFoundError:
    print("WARN_LOG (Simulador_PJ.py): Arquivo imgs/logo.png não encontrado.")
except Exception as e_img:
    print(f"WARN_LOG (Simulador_PJ.py): Erro ao carregar imgs/logo.png: {e_img}")

st.markdown("<h1 style='text-align: center; color: #54A033;'>Simulador de Venda - Pessoa Jurídica</h1>", unsafe_allow_html=True)
st.markdown("---")

st.write(f"Usuário: {current_name} ({current_username})")
st.write(f"Nível de Acesso: {current_role}") 
st.markdown("---")

planos = {
    "12 Meses": {
        "GPRS / Gsm": Decimal("80.88"), "Satélite": Decimal("193.80"),
        "Identificador de Motorista / RFID": Decimal("19.25"),
        "Leitor de Rede CAN / Telemetria": Decimal("75.25"),
        "Videomonitoramento + DMS + ADAS": Decimal("409.11")
    },
    "24 Meses": {
        "GPRS / Gsm": Decimal("53.92"), "Satélite": Decimal("129.20"),
        "Identificador de Motorista / RFID": Decimal("12.83"),
        "Leitor de Rede CAN / Telemetria": Decimal("50.17"),
        "Videomonitoramento + DMS + ADAS": Decimal("272.74")
    },
    "36 Meses": {
        "GPRS / Gsm": Decimal("44.93"), "Satélite": Decimal("107.67"),
        "Identificador de Motorista / RFID": Decimal("10.69"),
        "Leitor de Rede CAN / Telemetria": Decimal("41.81"),
        "Videomonitoramento + DMS + ADAS": Decimal("227.28")
    }
}

produtos_descricao = {
    "GPRS / Gsm": "Equipamento de rastreamento GSM/GPRS 2G ou 4G",
    "Satélite": "Equipamento de rastreamento via satélite",
    "Identificador de Motorista / RFID": "Identificação automática de motoristas via RFID",
    "Leitor de Rede CAN / Telemetria": "Leitura de dados de telemetria via rede CAN",
    "Videomonitoramento + DMS + ADAS": "Sistema de videomonitoramento com assistência ao motorista"
}

st.sidebar.header("📝 Configurações PJ") 
qtd_veiculos_key = "pj_qtd_veiculos_sb_v2" # Chaves atualizadas
temp_contrato_key = "pj_temp_contrato_sb_v2"

qtd_veiculos = st.sidebar.number_input("Quantidade de Veículos 🚗", min_value=1, value=1, key=qtd_veiculos_key)
temp_contrato_selecionado = st.sidebar.selectbox("Tempo de Contrato ⏳", list(planos.keys()), key=temp_contrato_key)

st.markdown("### 🛠️ Selecione os Produtos:")
col1_pj, col2_pj = st.columns(2) 
produtos_selecionados_pj = {} 

for i, (produto, preco) in enumerate(planos[temp_contrato_selecionado].items()):
    col_target = col1_pj if i % 2 == 0 else col2_pj
    produto_toggle_key = f"pj_toggle_{produto.replace(' ', '_').replace('/', '_').replace('+', '')}_v2" # Chave mais robusta
    if col_target.toggle(f"{produto} - R$ {preco:,.2f}", key=produto_toggle_key):
        produtos_selecionados_pj[produto] = preco 

soma_mensal_produtos_selecionados = sum(produtos_selecionados_pj.values()) 
valor_mensal_total_frota = soma_mensal_produtos_selecionados * Decimal(str(qtd_veiculos)) 
meses_contrato = Decimal(temp_contrato_selecionado.split()[0]) 
valor_total_contrato = valor_mensal_total_frota * meses_contrato

st.markdown("---")
if produtos_selecionados_pj: 
    st.success(f"✅ Valor Mensal por Veículo (soma dos produtos): R$ {soma_mensal_produtos_selecionados:,.2f}")
    st.info(f"💰 Valor Mensal Total para a Frota ({qtd_veiculos} veíc.): R$ {valor_mensal_total_frota:,.2f}")
    st.info(f"📄 Valor Total do Contrato ({temp_contrato_selecionado}): R$ {valor_total_contrato:,.2f}")
else:
    st.info("Selecione produtos para ver o cálculo.")


if st.button("🔄 Limpar Seleção e Recalcular", key="pj_btn_limpar_recalcular_v2"):
    st.rerun()

# Formulário para Gerar Proposta
if produtos_selecionados_pj: 
    if API_KEY_CLOUDCONVERT: # Só mostra o formulário se a API Key estiver presente
        st.markdown("---")
        st.subheader("📄 Gerar Proposta em PDF")

        with st.form("formulario_proposta_pj_v2", key="pj_form_proposta_v2"): 
            nome_empresa = st.text_input("Nome da Empresa", key="pj_form_nome_empresa_v2")
            nome_responsavel = st.text_input("Nome do Responsável", key="pj_form_nome_responsavel_v2")
            nome_consultor = st.text_input("Nome do Consultor Comercial", key="pj_form_nome_consultor_v2")
            validade_proposta_dt = st.date_input("Validade da Proposta", value=datetime.today(), key="pj_form_validade_proposta_v2")
            
            gerar_proposta_btn = st.form_submit_button("Gerar Proposta")

        if gerar_proposta_btn:
            print(f"INFO_LOG (Simulador_PJ.py): Botão 'Gerar Proposta' clicado. Empresa: {nome_empresa}")
            if not all([nome_empresa, nome_responsavel, nome_consultor]):
                st.warning("Por favor, preencha todos os dados da proposta (Empresa, Responsável, Consultor).")
            else:
                try:
                    # Caminho para o template DOCX
                    doc_template_path = "Proposta Comercial e Intenção - Verdio.docx" #
                    doc = Document(doc_template_path) 
                    print(f"INFO_LOG (Simulador_PJ.py): Template DOCX '{doc_template_path}' carregado.")

                    # Substituições no texto
                    for p in doc.paragraphs:
                        if "Nome da empresa" in p.text: p.text = p.text.replace("Nome da empresa", nome_empresa)
                        if "Nome do Responsável" in p.text: p.text = p.text.replace("Nome do Responsável", nome_responsavel)
                        if "00/00/0000" in p.text: p.text = p.text.replace("00/00/0000", validade_proposta_dt.strftime("%d/%m/%Y"))
                        if "Nome do comercial" in p.text: p.text = p.text.replace("Nome do comercial", nome_consultor)

                    # Substituições na tabela de produtos
                    table_found = False
                    for table in doc.tables:
                        if any("Item" in cell.text for cell in table.rows[0].cells): 
                            table_found = True
                            while len(table.rows) > 1:
                                table._tbl.remove(table.rows[1]._tr)
                            
                            for produto_sel, preco_sel in produtos_selecionados_pj.items():
                                row_cells = table.add_row().cells
                                row_cells[0].text = produto_sel
                                row_cells[1].text = produtos_descricao.get(produto_sel, " ") # Descrição ou vazio
                                row_cells[2].text = f"R$ {preco_sel:,.2f}" 
                            
                            total_row = table.add_row().cells
                            total_row[0].text = "TOTAL MENSAL POR VEÍCULO"
                            total_row[0].paragraphs[0].runs[0].font.bold = True
                            total_row[1].text = "" 
                            total_row[2].text = f"R$ {soma_mensal_produtos_selecionados:,.2f}"
                            total_row[2].paragraphs[0].runs[0].font.bold = True
                            break 
                    if not table_found:
                        print("WARN_LOG (Simulador_PJ.py): Tabela de itens não encontrada no template DOCX.")
                        st.warning("A tabela de itens não foi encontrada no template do documento.")


                    buffer_docx = BytesIO()
                    doc.save(buffer_docx)
                    buffer_docx.seek(0)
                    print("INFO_LOG (Simulador_PJ.py): DOCX da proposta gerado em buffer.")

                    with st.spinner("Gerando PDF da proposta, aguarde... (Pode levar alguns instantes)"):
                        headers = {"Authorization": f"Bearer {API_KEY_CLOUDCONVERT}"}
                        job_payload = {
                            "tasks": {
                                "import-docx": {"operation": "import/upload"},
                                "convert-to-pdf": {"operation": "convert", "input": "import-docx", "input_format": "docx", "output_format": "pdf", "engine": "libreoffice"},
                                "export-pdf": {"operation": "export/url", "input": "convert-to-pdf", "inline": False, "archive_multiple_files": False}
                            }
                        }
                        job_response = requests.post('https://api.cloudconvert.com/v2/jobs', json=job_payload, headers=headers)
                        job_response.raise_for_status() 
                        job_data = job_response.json()
                        
                        upload_task_id = None
                        for task_name, task_details in job_data['data']['tasks'].items():
                            if task_details['operation'] == 'import/upload':
                                upload_task_id = task_details['id']
                                upload_url = task_details['result']['form']['url']
                                parameters = task_details['result']['form']['parameters']
                                break
                        
                        if not upload_task_id:
                            st.error("Não foi possível encontrar a tarefa de upload no job do CloudConvert.")
                            raise Exception("Tarefa de upload não encontrada no CloudConvert.")

                        
                        files_payload = {'file': (f'proposta_{nome_empresa.replace(" ", "_")}.docx', buffer_docx, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')}
                        upload_response = requests.post(upload_url, data=parameters, files=files_payload)
                        upload_response.raise_for_status()
                        print(f"INFO_LOG (Simulador_PJ.py): DOCX enviado para CloudConvert. Upload Status: {upload_response.status_code}")

                        job_id = job_data['data']['id']
                        status_check_url = f'https://api.cloudconvert.com/v2/jobs/{job_id}'
                        
                        max_wait_time = 120 
                        start_time = time.time()
                        pdf_url = None
                        while time.time() - start_time < max_wait_time:
                            check_response = requests.get(status_check_url, headers=headers)
                            check_response.raise_for_status()
                            check_data = check_response.json()
                            job_status = check_data['data']['status']
                            print(f"DEBUG_LOG (Simulador_PJ.py): Status do job CloudConvert '{job_id}': {job_status}")
                            
                            if job_status == 'finished':
                                for task in check_data['data']['tasks']:
                                    if task.get('operation') == 'export/url' and task.get('status') == 'finished': # Nome da tarefa pode variar
                                        if task.get('result') and task['result'].get('files'):
                                            pdf_url = task['result']['files'][0]['url']
                                            break
                                if pdf_url: break # Sai do while se encontrou a URL
                            elif job_status == 'error':
                                error_message = "Erro desconhecido do CloudConvert."
                                if check_data['data'].get('tasks'):
                                    for task in check_data['data']['tasks']:
                                        if task.get('status') == 'error':
                                            error_message = task.get('message', error_message)
                                            if task.get('result') and task['result'].get('errors'):
                                                error_message += f" Detalhes: {task['result']['errors']}"
                                            break
                                st.error(f"Erro na conversão para PDF: {error_message}")
                                print(f"ERROR_LOG (Simulador_PJ.py): Erro no job CloudConvert '{job_id}': {check_data['data']}")
                                break
                            time.sleep(3) 
                        
                        if pdf_url:
                            print(f"INFO_LOG (Simulador_PJ.py): PDF gerado. URL: {pdf_url}")
                            pdf_response_content = requests.get(pdf_url).content
                            st.download_button(
                                label="📥 Baixar Proposta em PDF",
                                data=pdf_response_content,
                                file_name=f"Proposta_Verdio_{nome_empresa.replace(' ', '_')}_{validade_proposta_dt.strftime('%Y%m%d')}.pdf",
                                mime="application/pdf",
                                key="pj_download_pdf_btn_v2"
                            )
                        elif job_status != 'error': 
                            st.error("Erro ao finalizar a exportação do PDF ou tempo de espera excedido.")
                            print(f"ERROR_LOG (Simulador_PJ.py): Job CloudConvert '{job_id}' finalizado sem URL ou timeout.")

                except FileNotFoundError:
                    st.error(f"ERRO: O arquivo template '{doc_template_path}' não foi encontrado. Verifique o caminho no seu repositório.")
                    print(f"ERROR_LOG (Simulador_PJ.py): Template DOCX '{doc_template_path}' não encontrado.")
                except requests.exceptions.RequestException as req_e:
                    st.error(f"Erro de comunicação com o serviço CloudConvert: {req_e}")
                    print(f"ERROR_LOG (Simulador_PJ.py): CloudConvert RequestException: {req_e}")
                except Exception as e_gerar:
                    st.error(f"Ocorreu um erro inesperado ao gerar a proposta: {e_gerar}")
                    print(f"ERROR_LOG (Simulador_PJ.py): Erro na geração da proposta: {type(e_gerar).__name__} - {e_gerar}")

elif produtos_selecionados_pj and not API_KEY_CLOUDCONVERT: # Se há produtos mas não há API Key
    st.markdown("---")
    st.warning("⚠️ A funcionalidade de gerar proposta em PDF está desativada porque a chave da API do CloudConvert não está configurada nos segredos do aplicativo.")
    print("WARN_LOG (Simulador_PJ.py): Tentativa de gerar PDF sem CLOUDCONVERT_API_KEY configurada.")