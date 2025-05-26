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
# O st.secrets.get() é usado para evitar um KeyError se a chave não existir,
# retornando None por padrão nesse caso.
API_KEY_CLOUDCONVERT = st.secrets.get("CLOUDCONVERT_API_KEY") 
api_key_presente = bool(API_KEY_CLOUDCONVERT) # True se a chave existir e não for vazia

if not api_key_presente:
    print("WARN_LOG (Simulador_PJ.py): CLOUDCONVERT_API_KEY não configurada nos segredos do aplicativo.")
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
qtd_veiculos_key = "pj_qtd_veiculos_sb_v4" # Chaves atualizadas para garantir unicidade
temp_contrato_key = "pj_temp_contrato_sb_v4"

qtd_veiculos = st.sidebar.number_input("Quantidade de Veículos 🚗", min_value=1, value=1, key=qtd_veiculos_key)
temp_contrato_selecionado = st.sidebar.selectbox("Tempo de Contrato ⏳", list(planos.keys()), key=temp_contrato_key)

st.markdown("### 🛠️ Selecione os Produtos:")
col1_pj, col2_pj = st.columns(2) 
produtos_selecionados_pj = {} 

for i, (produto, preco) in enumerate(planos[temp_contrato_selecionado].items()):
    col_target = col1_pj if i % 2 == 0 else col2_pj
    # Chave de toggle mais robusta e única
    produto_toggle_key = f"pj_toggle_{temp_contrato_selecionado.replace(' ','_')}_{produto.replace(' ', '_').replace('/', '_').replace('+', '')}_v4" 
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


if st.button("🔄 Limpar Seleção e Recalcular", key="pj_btn_limpar_recalcular_v4"):
    st.rerun()

# Formulário para Gerar Proposta
if produtos_selecionados_pj: 
    st.markdown("---")
    st.subheader("📄 Gerar Proposta em PDF")

    # Exibe o aviso FORA do formulário se a API Key não estiver presente
    if not api_key_presente:
        st.warning("⚠️ A funcionalidade de gerar proposta em PDF está desativada porque a chave da API do CloudConvert não está configurada nos segredos do aplicativo.")
        print("WARN_LOG (Simulador_PJ.py): Formulário de proposta mostrado, mas PDF desativado por falta de API Key.")

    # O formulário é sempre exibido se houver produtos, mas o botão de submit pode ser desabilitado
    with st.form("formulario_proposta_pj_v4", key="pj_form_proposta_v4"): 
        nome_empresa = st.text_input("Nome da Empresa", key="pj_form_nome_empresa_v4")
        nome_responsavel = st.text_input("Nome do Responsável", key="pj_form_nome_responsavel_v4")
        nome_consultor = st.text_input("Nome do Consultor Comercial", key="pj_form_nome_consultor_v4")
        validade_proposta_dt = st.date_input("Validade da Proposta", value=datetime.today(), key="pj_form_validade_proposta_v4")
        
        # O botão "Gerar Proposta" só fica habilitado se a API Key estiver presente
        gerar_proposta_btn = st.form_submit_button("Gerar Proposta", disabled=(not api_key_presente))

    if gerar_proposta_btn and api_key_presente: # Verifica novamente se a chave está presente antes de prosseguir
        print(f"INFO_LOG (Simulador_PJ.py): Botão 'Gerar Proposta' clicado. Empresa: {nome_empresa}")
        if not all([nome_empresa, nome_responsavel, nome_consultor]):
            st.warning("Por favor, preencha todos os dados da proposta (Empresa, Responsável, Consultor).")
        else:
            # Envolve a lógica de geração de documento em um try-except
            try:
                # Caminho para o template DOCX - Verifique se este arquivo está na raiz do seu repositório
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
                    # Identifica a tabela de itens de forma mais robusta (ex: verificando múltiplos cabeçalhos)
                    header_texts = [cell.text.strip() for cell in table.rows[0].cells]
                    if "Item" in header_texts and "Descrição" in header_texts and "Valor Mensal" in header_texts: 
                        table_found = True
                        # Limpa linhas antigas (exceto o cabeçalho)
                        while len(table.rows) > 1:
                            table._tbl.remove(table.rows[1]._tr) # Acessa o elemento XML da tabela para remover a linha
                        
                        # Adiciona novos produtos selecionados
                        for produto_sel, preco_sel in produtos_selecionados_pj.items():
                            row_cells = table.add_row().cells
                            row_cells[0].text = produto_sel
                            row_cells[1].text = produtos_descricao.get(produto_sel, " ") # Descrição ou vazio se não encontrada
                            row_cells[2].text = f"R$ {preco_sel:,.2f}" # Preço mensal unitário
                        
                        # Adiciona linha de TOTAL MENSAL POR VEÍCULO
                        total_row = table.add_row().cells
                        total_row[0].text = "TOTAL MENSAL POR VEÍCULO"
                        total_row[0].paragraphs[0].runs[0].font.bold = True # Deixa o texto em negrito
                        total_row[1].text = "" # Coluna de descrição vazia para o total
                        total_row[2].text = f"R$ {soma_mensal_produtos_selecionados:,.2f}"
                        total_row[2].paragraphs[0].runs[0].font.bold = True # Deixa o texto em negrito
                        break # Assume que encontrou e preencheu a tabela correta
                
                if not table_found:
                    print("WARN_LOG (Simulador_PJ.py): Tabela de itens não encontrada ou não corresponde ao formato esperado no template DOCX.")
                    st.warning("A tabela de itens não foi encontrada ou não corresponde ao formato esperado no template do documento.")


                buffer_docx = BytesIO()
                doc.save(buffer_docx)
                buffer_docx.seek(0)
                print("INFO_LOG (Simulador_PJ.py): DOCX da proposta gerado em buffer.")

                # Lógica de conversão para PDF com CloudConvert
                with st.spinner("Gerando PDF da proposta, aguarde... (Pode levar alguns instantes)"):
                    headers = {"Authorization": f"Bearer {API_KEY_CLOUDCONVERT}"} # Usa a chave lida dos segredos
                    job_payload = {
                        "tasks": {
                            "import-docx": {"operation": "import/upload", "filename": f"proposta_{nome_empresa.replace(' ', '_')}.docx"},
                            "convert-to-pdf": {
                                "operation": "convert", 
                                "input": "import-docx", 
                                "input_format": "docx", 
                                "output_format": "pdf", 
                                "engine": "libreoffice" # Especifica o motor de conversão
                            },
                            "export-pdf": {
                                "operation": "export/url", 
                                "input": "convert-to-pdf", 
                                "inline": False, # Para obter um link de download direto
                                "archive_multiple_files": False
                            }
                        }
                    }
                    # Cria o job no CloudConvert
                    job_creation_response = requests.post('https://api.cloudconvert.com/v2/jobs', json=job_payload, headers=headers)
                    job_creation_response.raise_for_status() # Levanta erro HTTP se a criação do job falhar
                    job_data = job_creation_response.json()
                    
                    # Encontra a tarefa de upload e seus parâmetros
                    upload_task_id = None
                    upload_url = None
                    upload_parameters = None
                    for task_details in job_data['data']['tasks']: # Itera sobre a lista de tarefas
                        if task_details['operation'] == 'import/upload':
                            upload_task_id = task_details['id']
                            if task_details.get('result') and task_details['result'].get('form'):
                                upload_url = task_details['result']['form'].get('url')
                                upload_parameters = task_details['result']['form'].get('parameters')
                            break 
                    
                    if not upload_url or upload_parameters is None: # Verifica se os parâmetros foram encontrados
                        st.error("Não foi possível obter URL/parâmetros de upload do CloudConvert após criar o job.")
                        print(f"ERROR_LOG (Simulador_PJ.py): Falha ao obter URL/parâmetros de upload. Job data: {job_data}")
                        st.stop() # Interrompe se não puder prosseguir
                    
                    # Faz o upload do arquivo DOCX
                    files_payload_for_upload = {'file': (f'proposta_{nome_empresa.replace(" ", "_")}.docx', buffer_docx, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')}
                    upload_post_response = requests.post(upload_url, data=upload_parameters, files=files_payload_for_upload)
                    upload_post_response.raise_for_status() # Levanta erro se o upload falhar
                    print(f"INFO_LOG (Simulador_PJ.py): DOCX enviado para CloudConvert. Upload Status: {upload_post_response.status_code}")

                    job_id = job_data['data']['id']
                    status_check_url = f'https://api.cloudconvert.com/v2/jobs/{job_id}'
                    
                    # Espera o processamento do job
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
                                        break # Encontrou a URL do PDF
                            if pdf_download_url: break # Sai do loop while
                        elif current_job_status == 'error':
                            final_job_status = 'error'
                            # Tenta pegar uma mensagem de erro mais detalhada
                            error_message_from_cloudconvert = "Erro desconhecido do CloudConvert."
                            if job_status_data['data'].get('tasks'):
                                for task_data_loop in job_status_data['data']['tasks']:
                                    if task_data_loop.get('status') == 'error':
                                        error_message_from_cloudconvert = task_data_loop.get('message', error_message_from_cloudconvert)
                                        if task_data_loop.get('result') and task_data_loop['result'].get('errors'):
                                            error_message_from_cloudconvert += f" Detalhes: {task_data_loop['result']['errors']}"
                                        break
                            st.error(f"Erro na conversão para PDF via CloudConvert: {error_message_from_cloudconvert}")
                            print(f"ERROR_LOG (Simulador_PJ.py): Erro no job CloudConvert '{job_id}': {job_status_data['data']}")
                            break # Sai do loop while em caso de erro
                        time.sleep(3) # Pausa antes de verificar o status novamente
                    
                    if pdf_download_url:
                        print(f"INFO_LOG (Simulador_PJ.py): PDF gerado com sucesso. URL para download: {pdf_download_url}")
                        pdf_file_content = requests.get(pdf_download_url).content # Baixa o conteúdo do PDF
                        st.download_button(
                            label="📥 Baixar Proposta em PDF",
                            data=pdf_file_content,
                            file_name=f"Proposta_Verdio_{nome_empresa.replace(' ', '_')}_{validade_proposta_dt.strftime('%Y%m%d')}.pdf",
                            mime="application/pdf",
                            key="pj_download_pdf_btn_v4" # Chave única para o botão de download
                        )
                    elif final_job_status != 'error': # Se não houve erro explícito, mas não obteve URL (ex: timeout)
                        st.error("Não foi possível obter o arquivo PDF finalizado do CloudConvert ou o tempo de espera foi excedido.")
                        print(f"ERROR_LOG (Simulador_PJ.py): Job CloudConvert '{job_id}' finalizado sem URL de PDF ou timeout.")

            except FileNotFoundError:
                st.error(f"ERRO: O arquivo template DOCX '{doc_template_path}' não foi encontrado. Verifique o caminho no seu repositório.")
                print(f"ERROR_LOG (Simulador_PJ.py): Template DOCX '{doc_template_path}' não encontrado.")
            except requests.exceptions.RequestException as req_e:
                st.error(f"Erro de comunicação com o serviço CloudConvert: {req_e}")
                print(f"ERROR_LOG (Simulador_PJ.py): CloudConvert RequestException: {req_e}")
            except Exception as e_gerar:
                st.error(f"Ocorreu um erro inesperado ao gerar a proposta: {e_gerar}")
                print(f"ERROR_LOG (Simulador_PJ.py): Erro na geração da proposta: {type(e_gerar).__name__} - {e_gerar}")
    
elif not API_KEY_CLOUDCONVERT and produtos_selecionados_pj: 
    # Este aviso é mostrado se há produtos mas a API Key não está configurada
    # O formulário acima já terá o botão "Gerar Proposta" desabilitado neste caso.
    # st.warning("⚠️ A funcionalidade de gerar proposta em PDF está desativada porque a chave da API do CloudConvert não está configurada.")
    pass # O aviso já é mostrado acima do formulário

elif not produtos_selecionados_pj: 
    st.info("Selecione produtos para poder preencher os dados e gerar uma proposta.")