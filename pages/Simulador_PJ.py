# pages/Simulador_PJ.py
# Importações Python padrão primeiro
from io import BytesIO
from docx import Document 
from docx.shared import Pt
import requests
import time
from datetime import datetime
from decimal import Decimal, ROUND_DOWN # Se for usar Decimal para os preços

import streamlit as st

# 1. st.set_page_config() - PRIMEIRO COMANDO STREAMLIT
st.set_page_config(
    layout="wide",
    page_title="Simulador Pessoa Jurídica", 
    page_icon="imgs/v-c.png", # Verifique se o caminho está correto
    initial_sidebar_state="expanded"
)
print("INFO_LOG (Simulador_PJ.py): st.set_page_config executado.")

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

print(f"INFO_LOG (Simulador_PJ.py): User '{current_username}' authenticated. Role: '{current_role}'. Iniciando renderização da página...")

# 3. Restante do código da sua página

# 🛡️ Token CloudConvert - Idealmente, pegue de st.secrets
# Para depuração, vamos verificar se a chave que você colou está sendo lida.
# No entanto, para o Streamlit Cloud, o ideal é st.secrets.get("CLOUDCONVERT_API_KEY")
HARDCODED_API_KEY = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJhdWQiOiIxIiwianRpIjoiZmNhNjY2Y2E5NzEyMGYzNTgxM2IwNDVkMjA4OTYxODM1NGQxNjU0NjBkZjE1M2QwYzBiZjM4MjA5NGMxZDdjODUxMTg2Mzc1OTUxMDRhZDkiLCJpYXQiOjE3NDU4NzYwNTEuMjUwNjg1LCJuYmYiOjE3NDU4NzYwNTEuMjUwNjg2LCJleHAiOjQ5MDE1NDk2NTEuMjQ0MjU3LCJzdWIiOiI3MTc3MDMzMSIsInNjb3BlcyI6WyJ3ZWJob29rLndyaXRlIiwid2ViaG9vay5yZWFkIiwidGFzay53cml0ZSIsInRhc2sucmVhZCJdfQ.chEPyU6axXxsQTOqAvRg9qzKZP_gOgaKC4OyWuCPZDrwctEW63d-4hRt-4W9FL-aSqTcaXreBn2nax94T4zl_APuZj4bcRJefga8-uOhqWrUX6cAHjumev-BXILmtxi0XbgXkz4wZ-rsVP3-ETCfYq-GPYTnU-va6MgclBtVMOMM6I9-Yh-sCHiYBawPR_zzoHxk6j880I1CVHg42yGHfcIw83gq6Jfle7PrZaScPh3PzBl97STdRUeuaw6pwaTC8CPCTHV3YA3XU3JQd7i1o2t2PerMXuD79dk45NZxvJX8KJCcPtvnNCGFrI677X3nLfo86eUgnqtLbrRO1COhtU5spZUTNWqms2pGLfJFgotRUAc9T3NLHjVWF3841v0MjcIr1dLXFgf0KMbmI0pBmmotFw7t29Juid1pv5evRIRpYSbEvCNrpg9uIXlxPVPM863aZbBvqSalQAsYwkdv0Wvw16Z7cm2dgqHY-Xpv0I8Yubv61OJ4yirZPQNkXVoV-4DIFY-IHkRyX3C7fYwnAWXyK8wnskrDfHm5yegTVPduVmp8RzeH8WMSBmPlDLsU7KXc_4FhR212A5fzlfKhgVqIUlHKzoq-S-kyigNUUrSQt4ugYKX_2kEZKZMs6UMqt7MHTU7mLT1QWZOmMFBSDReHV0QwwLsKkaP4jkMNKoQ"
API_KEY_FROM_SECRETS = st.secrets.get("CLOUDCONVERT_API_KEY")

if API_KEY_FROM_SECRETS:
    API_KEY = API_KEY_FROM_SECRETS
    print("INFO_LOG (Simulador_PJ.py): Usando CLOUDCONVERT_API_KEY dos segredos.")
else:
    API_KEY = HARDCODED_API_KEY # Fallback para a chave hardcoded (NÃO RECOMENDADO PARA PRODUÇÃO)
    print("WARN_LOG (Simulador_PJ.py): CLOUDCONVERT_API_KEY não encontrada nos segredos. Usando chave hardcoded (se houver).")
    if not API_KEY: # Se a hardcoded também estiver vazia/None
        st.warning("⚠️ Chave da API do CloudConvert não configurada. Geração de PDF estará desativada.")
        print("ERROR_LOG (Simulador_PJ.py): Nenhuma API Key do CloudConvert disponível.")

api_key_presente_para_pdf = bool(API_KEY)


# 🔵 Logotipo e cabeçalho estilizado
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
print("INFO_LOG (Simulador_PJ.py): Cabeçalho e informações do usuário renderizados.")

# Produtos (convertendo para Decimal na definição)
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

# Sidebar
st.sidebar.header("📝 Configurações PJ") 
# Chaves únicas para widgets da sidebar
qtd_veiculos_key = "pj_qtd_veiculos_sb_v5" 
temp_contrato_key = "pj_temp_contrato_sb_v5"

qtd_veiculos_input = st.sidebar.number_input("Quantidade de Veículos 🚗", min_value=1, value=1, step=1, key=qtd_veiculos_key)
temp_contrato_selecionado = st.sidebar.selectbox("Tempo de Contrato ⏳", list(planos.keys()), key=temp_contrato_key)
print("INFO_LOG (Simulador_PJ.py): Widgets da sidebar renderizados.")

# Seção principal
st.markdown("### 🛠️ Selecione os Produtos:")
col1_pj, col2_pj = st.columns(2) 
produtos_selecionados_pj = {} 

for i, (produto, preco_decimal) in enumerate(planos[temp_contrato_selecionado].items()): # preco_decimal já é Decimal
    col_target = col1_pj if i % 2 == 0 else col2_pj
    produto_toggle_key = f"pj_toggle_{temp_contrato_selecionado.replace(' ','_')}_{produto.replace(' ', '_').replace('/', '_').replace('+', '')}_v5" 
    if col_target.toggle(f"{produto} - R$ {preco_decimal:,.2f}", key=produto_toggle_key):
        produtos_selecionados_pj[produto] = preco_decimal 

print(f"DEBUG_LOG (Simulador_PJ.py): Produtos selecionados: {produtos_selecionados_pj}")

# Cálculos
soma_mensal_produtos_selecionados = sum(produtos_selecionados_pj.values()) if produtos_selecionados_pj else Decimal("0")
qtd_veiculos_decimal = Decimal(str(qtd_veiculos_input)) # Converte para Decimal
valor_mensal_total_frota = soma_mensal_produtos_selecionados * qtd_veiculos_decimal
meses_contrato = Decimal(temp_contrato_selecionado.split()[0]) 
valor_total_contrato = valor_mensal_total_frota * meses_contrato

st.markdown("---")
if produtos_selecionados_pj: 
    st.success(f"✅ Valor Mensal por Veículo (soma dos produtos): R$ {soma_mensal_produtos_selecionados:,.2f}")
    st.info(f"💰 Valor Mensal Total para a Frota ({qtd_veiculos_input} veíc.): R$ {valor_mensal_total_frota:,.2f}")
    st.info(f"📄 Valor Total do Contrato ({temp_contrato_selecionado}): R$ {valor_total_contrato:,.2f}")
else:
    st.info("Selecione produtos para ver o cálculo.")
print("INFO_LOG (Simulador_PJ.py): Seção de cálculo de totais renderizada.")

if st.button("🔄 Limpar Seleção e Recalcular", key="pj_btn_limpar_recalcular_v5"):
    print("INFO_LOG (Simulador_PJ.py): Botão 'Limpar Seleção' clicado.")
    st.rerun()

# Formulário para Gerar Proposta
if produtos_selecionados_pj: 
    st.markdown("---")
    st.subheader("📄 Gerar Proposta em PDF")

    if not api_key_presente_para_pdf:
        st.warning("⚠️ A funcionalidade de gerar proposta em PDF está desativada porque a chave da API do CloudConvert não está configurada nos segredos do aplicativo.")
        print("WARN_LOG (Simulador_PJ.py): Geração de PDF desativada (API Key ausente).")

    with st.form("formulario_proposta_pj_v5", key="pj_form_proposta_v5"): 
        nome_empresa = st.text_input("Nome da Empresa", key="pj_form_nome_empresa_v5")
        nome_responsavel = st.text_input("Nome do Responsável", key="pj_form_nome_responsavel_v5")
        nome_consultor = st.text_input("Nome do Consultor Comercial", key="pj_form_nome_consultor_v5")
        validade_proposta_dt = st.date_input("Validade da Proposta", value=datetime.today(), key="pj_form_validade_proposta_v5")
        
        gerar_proposta_btn = st.form_submit_button("Gerar Proposta", disabled=(not api_key_presente_para_pdf))

    if gerar_proposta_btn and api_key_presente_para_pdf: 
        print(f"INFO_LOG (Simulador_PJ.py): Botão 'Gerar Proposta' clicado. Empresa: {nome_empresa}")
        if not all([nome_empresa, nome_responsavel, nome_consultor]):
            st.warning("Por favor, preencha todos os dados da proposta (Empresa, Responsável, Consultor).")
        else:
            try:
                doc_template_path = "Proposta Comercial e Intenção - Verdio.docx" #
                doc = Document(doc_template_path) 
                print(f"INFO_LOG (Simulador_PJ.py): Template DOCX '{doc_template_path}' carregado.")

                for p in doc.paragraphs:
                    if "Nome da empresa" in p.text: p.text = p.text.replace("Nome da empresa", nome_empresa)
                    if "Nome do Responsável" in p.text: p.text = p.text.replace("Nome do Responsável", nome_responsavel)
                    if "00/00/0000" in p.text: p.text = p.text.replace("00/00/0000", validade_proposta_dt.strftime("%d/%m/%Y"))
                    if "Nome do comercial" in p.text: p.text = p.text.replace("Nome do comercial", nome_consultor)

                table_found = False
                for table in doc.tables:
                    header_texts = [cell.text.strip() for cell in table.rows[0].cells]
                    if "Item" in header_texts and "Descrição" in header_texts and "Valor Mensal" in header_texts: 
                        table_found = True
                        while len(table.rows) > 1:
                            table._tbl.remove(table.rows[1]._tr) 
                        for produto_sel, preco_sel in produtos_selecionados_pj.items():
                            row_cells = table.add_row().cells
                            row_cells[0].text = produto_sel
                            row_cells[1].text = produtos_descricao.get(produto_sel, " ") 
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
                    st.warning("A tabela de itens não foi encontrada no template.")

                buffer_docx = BytesIO()
                doc.save(buffer_docx)
                buffer_docx.seek(0)
                print("INFO_LOG (Simulador_PJ.py): DOCX da proposta gerado em buffer.")

                with st.spinner("Gerando PDF da proposta, aguarde..."):
                    headers = {"Authorization": f"Bearer {API_KEY}"} # Usa a API_KEY definida no início
                    job_payload = {
                        "tasks": {
                            "import-docx": {"operation": "import/upload", "filename": f"proposta_{nome_empresa.replace(' ', '_')}.docx"},
                            "convert-to-pdf": {"operation": "convert", "input": "import-docx", "input_format": "docx", "output_format": "pdf", "engine": "libreoffice"},
                            "export-pdf": {"operation": "export/url", "input": "convert-to-pdf", "inline": False, "archive_multiple_files": False}
                        }
                    }
                    job_creation_response = requests.post('https://api.cloudconvert.com/v2/jobs', json=job_payload, headers=headers)
                    job_creation_response.raise_for_status() 
                    job_data = job_creation_response.json()
                    
                    upload_task_id = None; upload_url = None; upload_parameters = None
                    for task_details in job_data['data']['tasks']:
                        if task_details['operation'] == 'import/upload':
                            upload_task_id = task_details['id']
                            if task_details.get('result') and task_details['result'].get('form'):
                                upload_url = task_details['result']['form'].get('url')
                                upload_parameters = task_details['result']['form'].get('parameters')
                            break 
                    
                    if not upload_url or upload_parameters is None:
                        st.error("Falha ao obter URL/parâmetros de upload do CloudConvert.")
                        print(f"ERROR_LOG (Simulador_PJ.py): Falha ao obter URL/parâmetros de upload. Job: {job_data}")
                        st.stop() 
                    
                    files_payload_for_upload = {'file': (f'proposta_{nome_empresa.replace(" ", "_")}.docx', buffer_docx, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')}
                    upload_post_response = requests.post(upload_url, data=upload_parameters, files=files_payload_for_upload)
                    upload_post_response.raise_for_status()
                    print(f"INFO_LOG (Simulador_PJ.py): DOCX enviado. Upload Status: {upload_post_response.status_code}")

                    job_id = job_data['data']['id']
                    status_check_url = f'https://api.cloudconvert.com/v2/jobs/{job_id}'
                    
                    max_wait_time_seconds = 120 
                    start_process_time = time.time()
                    pdf_download_url = None
                    final_job_status = None
                    while time.time() - start_process_time < max_wait_time_seconds:
                        job_status_response = requests.get(status_check_url, headers=headers)
                        job_status_response.raise_for_status()
                        job_status_data = job_status_response.json()
                        current_job_status = job_status_data['data']['status']
                        print(f"DEBUG_LOG (Simulador_PJ.py): Status do job CloudConvert '{job_id}': {current_job_status}")
                        
                        if current_job_status == 'finished':
                            final_job_status = 'finished'
                            for task_data_loop in job_status_data['data']['tasks']:
                                if task_data_loop.get('operation') == 'export/url' and task_data_loop.get('status') == 'finished': 
                                    if task_data_loop.get('result') and task_data_loop['result'].get('files') and len(task_data_loop['result']['files']) > 0:
                                        pdf_download_url = task_data_loop['result']['files'][0]['url']
                                        break 
                            if pdf_download_url: break 
                        elif current_job_status == 'error':
                            final_job_status = 'error'
                            error_message_from_cloudconvert = "Erro CloudConvert."
                            if job_status_data['data'].get('tasks'):
                                for task_data_loop in job_status_data['data']['tasks']:
                                    if task_data_loop.get('status') == 'error':
                                        error_message_from_cloudconvert = task_data_loop.get('message', error_message_from_cloudconvert)
                                        if task_data_loop.get('result') and task_data_loop['result'].get('errors'):
                                            error_message_from_cloudconvert += f" Detalhes: {task_data_loop['result']['errors']}"
                                        break
                            st.error(f"Erro na conversão PDF: {error_message_from_cloudconvert}")
                            print(f"ERROR_LOG (Simulador_PJ.py): Erro job CloudConvert '{job_id}': {job_status_data['data']}")
                            break 
                        time.sleep(3) 
                    
                    if pdf_download_url:
                        print(f"INFO_LOG (Simulador_PJ.py): PDF gerado. URL: {pdf_download_url}")
                        pdf_file_content = requests.get(pdf_download_url).content 
                        st.download_button(
                            label="📥 Baixar Proposta em PDF",
                            data=pdf_file_content,
                            file_name=f"Proposta_Verdio_{nome_empresa.replace(' ', '_')}_{validade_proposta_dt.strftime('%Y%m%d')}.pdf",
                            mime="application/pdf",
                            key="pj_download_pdf_btn_v5" 
                        )
                    elif final_job_status != 'error': 
                        st.error("Não foi possível obter o PDF ou tempo de espera excedido.")
                        print(f"ERROR_LOG (Simulador_PJ.py): Job CloudConvert '{job_id}' finalizado sem URL ou timeout.")

            except FileNotFoundError:
                st.error(f"ERRO: Template '{doc_template_path}' não encontrado.")
                print(f"ERROR_LOG (Simulador_PJ.py): Template DOCX '{doc_template_path}' não encontrado.")
            except requests.exceptions.RequestException as req_e:
                st.error(f"Erro de comunicação com CloudConvert: {req_e}")
                print(f"ERROR_LOG (Simulador_PJ.py): CloudConvert RequestException: {req_e}")
            except Exception as e_gerar:
                st.error(f"Erro inesperado ao gerar proposta: {e_gerar}")
                print(f"ERROR_LOG (Simulador_PJ.py): Erro na geração da proposta: {type(e_gerar).__name__} - {e_gerar}")
    
elif not api_key_presente_para_pdf and produtos_selecionados_pj: 
    # O aviso já é mostrado acima do formulário se a API Key não está presente.
    pass
elif not produtos_selecionados_pj: 
    st.info("Selecione produtos para preencher dados e gerar uma proposta.")

print("INFO_LOG (Simulador_PJ.py): Renderização da página concluída.")