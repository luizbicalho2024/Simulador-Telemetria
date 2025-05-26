# pages/Simulador_PJ.py
# Importações Python padrão primeiro
from io import BytesIO
from docx import Document 
from docx.shared import Pt 
# from docx.enum.text import WD_ALIGN_PARAGRAPH # Se for usar alinhamento
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
print("INFO_LOG (Simulador_PJ.py): st.set_page_config executado.")

# 2. BLOCO DE VERIFICAÇÃO DE AUTENTICAÇÃO
auth_status = st.session_state.get("authentication_status", False)
if auth_status is not True:
    st.error("🔒 Acesso Negado! Por favor, faça login na página principal para continuar.")
    print(f"ACCESS_DENIED_LOG (Simulador_PJ.py): User not authenticated. Status: {auth_status}")
    try:
        st.page_link("Simulador_Comercial.py", label="Ir para Login", icon="🏠") #
    except AttributeError: 
        st.info("Retorne à página principal para efetuar o login.")
    st.stop() 

current_username = st.session_state.get('username', 'N/A')
current_role = st.session_state.get('role', 'Indefinido') 
current_name = st.session_state.get('name', 'N/A')

print(f"INFO_LOG (Simulador_PJ.py): User '{current_username}' authenticated. Role: '{current_role}'.")

# 3. Restante do código da sua página

API_KEY_CLOUDCONVERT = st.secrets.get("CLOUDCONVERT_API_KEY") 
api_key_presente = bool(API_KEY_CLOUDCONVERT) 

if not api_key_presente:
    print("WARN_LOG (Simulador_PJ.py): CLOUDCONVERT_API_KEY não configurada nos segredos.")

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
qtd_veiculos_key = "pj_qtd_veiculos_sb_v12_final" 
temp_contrato_key = "pj_temp_contrato_sb_v12_final"

qtd_veiculos_input = st.sidebar.number_input("Quantidade de Veículos 🚗", min_value=1, value=1, step=1, key=qtd_veiculos_key)
temp_contrato_selecionado = st.sidebar.selectbox("Tempo de Contrato ⏳", list(planos.keys()), key=temp_contrato_key)
print("INFO_LOG (Simulador_PJ.py): Widgets da sidebar renderizados.")

st.markdown("### 🛠️ Selecione os Produtos:")
col1_pj, col2_pj = st.columns(2) 
produtos_selecionados_pj = {} 

for i, (produto, preco_decimal) in enumerate(planos[temp_contrato_selecionado].items()):
    col_target = col1_pj if i % 2 == 0 else col2_pj
    produto_toggle_key = f"pj_toggle_{temp_contrato_selecionado.replace(' ','_')}_{produto.replace(' ', '_').replace('/', '_').replace('+', '')}_v12_final" 
    if col_target.toggle(f"{produto} - R$ {preco_decimal:,.2f}", key=produto_toggle_key):
        produtos_selecionados_pj[produto] = preco_decimal 

print(f"DEBUG_LOG (Simulador_PJ.py): Produtos selecionados para proposta: {produtos_selecionados_pj}")

soma_mensal_produtos_selecionados_calculada = sum(produtos_selecionados_pj.values()) if produtos_selecionados_pj else Decimal("0")
qtd_veiculos_decimal = Decimal(str(qtd_veiculos_input)) 
valor_mensal_total_frota_calculado = soma_mensal_produtos_selecionados_calculada * qtd_veiculos_decimal
meses_contrato = Decimal(temp_contrato_selecionado.split()[0]) 
valor_total_contrato_calculado = valor_mensal_total_frota_calculado * meses_contrato

st.markdown("---")
if produtos_selecionados_pj: 
    st.success(f"✅ Valor Mensal por Veículo (soma dos produtos selecionados): R$ {soma_mensal_produtos_selecionados_calculada:,.2f}")
    st.info(f"💰 Valor Mensal Total para a Frota ({qtd_veiculos_input} veíc.): R$ {valor_mensal_total_frota_calculado:,.2f}")
    st.info(f"📄 Valor Total do Contrato ({temp_contrato_selecionado}): R$ {valor_total_contrato_calculado:,.2f}")
else:
    st.info("Selecione produtos para ver o cálculo.")
print("INFO_LOG (Simulador_PJ.py): Seção de cálculo de totais renderizada.")

if st.button("🔄 Limpar Seleção e Recalcular", key="pj_btn_limpar_recalcular_v12_final"):
    print("INFO_LOG (Simulador_PJ.py): Botão 'Limpar Seleção' clicado.")
    st.rerun()

# Formulário para Gerar Proposta
if produtos_selecionados_pj: 
    st.markdown("---")
    st.subheader("📄 Gerar Proposta")

    if not api_key_presente:
        st.warning("⚠️ A funcionalidade de gerar proposta em PDF (via CloudConvert) está desativada porque a chave da API do CloudConvert não está configurada nos segredos do aplicativo.")
        print("WARN_LOG (Simulador_PJ.py): Geração de PDF desativada (API Key CloudConvert ausente).")

    with st.form(f"formulario_proposta_pj_v12_final", clear_on_submit=True): 
        nome_empresa = st.text_input("Nome da Empresa", key="pj_form_nome_empresa_v12_final")
        nome_responsavel = st.text_input("Nome do Responsável", key="pj_form_nome_responsavel_v12_final")
        nome_consultor = st.text_input("Nome do Consultor Comercial", value=current_name, key="pj_form_nome_consultor_v12_final")
        validade_proposta_dt = st.date_input("Validade da Proposta", value=datetime.today(), key="pj_form_validade_proposta_v12_final")
        
        col_btn_form1, col_btn_form2 = st.columns(2)
        with col_btn_form1:
            gerar_docx_btn = st.form_submit_button("Gerar Proposta em DOCX")
        with col_btn_form2:
            gerar_pdf_cloudconvert_btn = st.form_submit_button("Gerar PDF (CloudConvert)", disabled=(not api_key_presente))

    # Lógica para gerar DOCX
    if gerar_docx_btn:
        print(f"INFO_LOG (Simulador_PJ.py): Botão 'Gerar DOCX' clicado. Empresa: {nome_empresa}")
        if not all([nome_empresa, nome_responsavel, nome_consultor]):
            st.warning("Preencha os dados da proposta (Empresa, Responsável, Consultor).")
        else:
            try:
                doc_template_path = "Proposta Comercial e Intenção - Verdio.docx" #
                doc = Document(doc_template_path) 
                print(f"INFO_LOG (Simulador_PJ.py): Template DOCX '{doc_template_path}' carregado para DOCX.")

                for p in doc.paragraphs: # Preenchimento dos parágrafos
                    if "Nome da empresa" in p.text: p.text = p.text.replace("Nome da empresa", nome_empresa)
                    if "Nome do Responsável" in p.text: p.text = p.text.replace("Nome do Responsável", nome_responsavel)
                    if "00/00/0000" in p.text: p.text = p.text.replace("00/00/0000", validade_proposta_dt.strftime("%d/%m/%Y"))
                    if "Nome do comercial" in p.text: p.text = p.text.replace("Nome do comercial", nome_consultor)

                # LÓGICA DE PREENCHIMENTO DA TABELA REVISADA
                table_to_fill = None
                expected_headers = ["Item", "Descrição", "Valor Mensal"] # Confirme estes cabeçalhos no seu DOCX
                print(f"DEBUG_LOG (Simulador_PJ.py): Cabeçalhos esperados na tabela: {expected_headers}")

                for table_idx, table in enumerate(doc.tables):
                    print(f"DEBUG_LOG (Simulador_PJ.py): Verificando Tabela {table_idx} no DOCX...")
                    if len(table.rows) > 0 and len(table.columns) >= len(expected_headers):
                        header_cells_text = [cell.text.strip() for cell in table.rows[0].cells[:len(expected_headers)]]
                        print(f"DEBUG_LOG (Simulador_PJ.py): Cabeçalhos encontrados na Tabela {table_idx}: {header_cells_text}")
                        # Verifica se todos os cabeçalhos esperados estão contidos nos cabeçalhos da tabela
                        if all(exp_h in hc_text for exp_h, hc_text in zip(expected_headers, header_cells_text)):
                            table_to_fill = table
                            print(f"INFO_LOG (Simulador_PJ.py): Tabela de itens para preenchimento encontrada (Índice: {table_idx}).")
                            break 
                
                if table_to_fill:
                    # Limpa todas as linhas da tabela, exceto a primeira (cabeçalho)
                    print(f"DEBUG_LOG (Simulador_PJ.py): Limpando linhas da tabela (exceto cabeçalho). Linhas antes: {len(table_to_fill.rows)}")
                    while len(table_to_fill.rows) > 1:
                        table_to_fill._tbl.remove(table_to_fill.rows[-1]._tr) # Remove a última linha
                    print(f"DEBUG_LOG (Simulador_PJ.py): Linhas após limpeza: {len(table_to_fill.rows)}")

                    print(f"DEBUG_LOG (Simulador_PJ.py): Itens SELECIONADOS para adicionar à tabela: {produtos_selecionados_pj}")
                    if not produtos_selecionados_pj:
                        print("WARN_LOG (Simulador_PJ.py): Nenhum produto selecionado para adicionar à tabela do DOCX.")
                        st.warning("Nenhum produto foi selecionado para a proposta.")
                    
                    for produto_sel, preco_sel_decimal in produtos_selecionados_pj.items():
                        row_cells = table_to_fill.add_row().cells
                        row_cells[0].text = produto_sel
                        row_cells[1].text = produtos_descricao.get(produto_sel, " ") # Usa .get() para segurança
                        row_cells[2].text = f"R$ {preco_sel_decimal:,.2f}"
                        print(f"DEBUG_LOG (Simulador_PJ.py): Adicionado à tabela: {produto_sel}, R$ {preco_sel_decimal:,.2f}")
                    
                    # Adiciona linha de TOTAL MENSAL POR VEÍCULO
                    total_row = table_to_fill.add_row().cells
                    total_row[0].text = "TOTAL MENSAL POR VEÍCULO"
                    total_row[0].paragraphs[0].runs[0].font.bold = True 
                    total_row[1].text = "" 
                    total_row[2].text = f"R$ {soma_mensal_produtos_selecionados_calculada:,.2f}" # Usa a soma correta
                    total_row[2].paragraphs[0].runs[0].font.bold = True
                    print(f"DEBUG_LOG (Simulador_PJ.py): Linha de total adicionada: R$ {soma_mensal_produtos_selecionados_calculada:,.2f}")
                else:
                    st.warning("A tabela de itens não foi encontrada no template do documento. Verifique os cabeçalhos ('Item', 'Descrição', 'Valor Mensal') no seu arquivo .docx. A proposta será gerada sem a tabela de itens.")
                    print("WARN_LOG (Simulador_PJ.py): Tabela de itens NÃO encontrada/preenchida no template DOCX.")

                buffer_docx = BytesIO()
                doc.save(buffer_docx)
                buffer_docx.seek(0)
                print("INFO_LOG (Simulador_PJ.py): DOCX da proposta gerado em buffer para download direto.")
                
                st.download_button(
                    label="📥 Baixar Proposta em DOCX",
                    data=buffer_docx,
                    file_name=f"Proposta_Verdio_{nome_empresa.replace(' ', '_')}_{validade_proposta_dt.strftime('%Y%m%d')}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    key="pj_download_docx_btn_v12_final" 
                )
                st.success("Proposta em DOCX pronta para download!")

            except FileNotFoundError:
                st.error(f"ERRO: O arquivo template DOCX '{doc_template_path}' não foi encontrado.")
                print(f"ERROR_LOG (Simulador_PJ.py): Template DOCX '{doc_template_path}' não encontrado.")
            except Exception as e_gerar_docx:
                st.error(f"Erro inesperado ao gerar proposta DOCX: {e_gerar_docx}")
                print(f"ERROR_LOG (Simulador_PJ.py): Erro na geração DOCX: {type(e_gerar_docx).__name__} - {e_gerar_docx}")

    # Lógica para gerar PDF via CloudConvert (se o botão for clicado e API Key presente)
    if gerar_pdf_cloudconvert_btn and api_key_presente: 
        print(f"INFO_LOG (Simulador_PJ.py): Botão 'Gerar PDF (CloudConvert)' clicado. Empresa: {nome_empresa}")
        if not all([nome_empresa, nome_responsavel, nome_consultor]):
            st.warning("Preencha os dados da proposta (Empresa, Responsável, Consultor).")
        else:
            # Gera o DOCX em memória primeiro (mesma lógica do botão DOCX)
            try:
                doc_template_path = "Proposta Comercial e Intenção - Verdio.docx" #
                doc = Document(doc_template_path)
                for p in doc.paragraphs: # Preenchimento dos parágrafos
                    if "Nome da empresa" in p.text: p.text = p.text.replace("Nome da empresa", nome_empresa)
                    if "Nome do Responsável" in p.text: p.text = p.text.replace("Nome do Responsável", nome_responsavel)
                    if "00/00/0000" in p.text: p.text = p.text.replace("00/00/0000", validade_proposta_dt.strftime("%d/%m/%Y"))
                    if "Nome do comercial" in p.text: p.text = p.text.replace("Nome do comercial", nome_consultor)
                
                table_to_fill_pdf = None
                expected_headers_pdf = ["Item", "Descrição", "Valor Mensal"] 
                for table_idx, table in enumerate(doc.tables):
                    if len(table.rows) > 0 and len(table.columns) >= len(expected_headers_pdf): 
                        header_cells_text_pdf = [cell.text.strip() for cell in table.rows[0].cells[:len(expected_headers_pdf)]]
                        if all(expected_header in header_cells_text_pdf for expected_header in expected_headers_pdf):
                            table_to_fill_pdf = table
                            break 
                
                if table_to_fill_pdf:
                    while len(table_to_fill_pdf.rows) > 1: table_to_fill_pdf._tbl.remove(table_to_fill_pdf.rows[-1]._tr) 
                    for produto_sel, preco_sel_decimal in produtos_selecionados_pj.items():
                        row_cells = table_to_fill_pdf.add_row().cells
                        row_cells[0].text = produto_sel
                        row_cells[1].text = produtos_descricao.get(produto_sel, " ") 
                        row_cells[2].text = f"R$ {preco_sel_decimal:,.2f}" 
                    total_row = table_to_fill_pdf.add_row().cells
                    total_row[0].text = "TOTAL MENSAL POR VEÍCULO"; total_row[0].paragraphs[0].runs[0].font.bold = True 
                    total_row[1].text = "" 
                    total_row[2].text = f"R$ {soma_mensal_produtos_selecionados_calculada:,.2f}"; total_row[2].paragraphs[0].runs[0].font.bold = True
                else:
                    st.warning("Tabela de itens não encontrada no template para PDF.")
                    print("WARN_LOG (Simulador_PJ.py): Tabela de itens não encontrada para PDF.")
                    st.stop()

                buffer_docx_for_pdf = BytesIO()
                doc.save(buffer_docx_for_pdf)
                buffer_docx_for_pdf.seek(0)
                print("INFO_LOG (Simulador_PJ.py): DOCX gerado para conversão PDF.")

                with st.spinner("Gerando PDF da proposta via CloudConvert, aguarde..."):
                    # ... (Lógica de comunicação com CloudConvert como na versão anterior) ...
                    # Certifique-se que API_KEY_CLOUDCONVERT está sendo usada nos headers.
                    headers = {"Authorization": f"Bearer {API_KEY_CLOUDCONVERT}"} 
                    # ... (resto da lógica do CloudConvert) ...
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
                        st.stop() 
                    
                    files_payload_for_upload = {'file': (f'proposta_{nome_empresa.replace(" ", "_")}.docx', buffer_docx_for_pdf, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')}
                    upload_post_response = requests.post(upload_url, data=upload_parameters, files=files_payload_for_upload)
                    upload_post_response.raise_for_status()

                    job_id = job_data['data']['id']
                    status_check_url = f'https://api.cloudconvert.com/v2/jobs/{job_id}'
                    
                    max_wait_time_seconds = 120 
                    start_process_time = time.time()
                    pdf_download_url = None
                    final_job_status = None
                    with st.empty(): 
                        while time.time() - start_process_time < max_wait_time_seconds:
                            st.write(f"Verificando status da conversão (Job ID: {job_id})...")
                            job_status_response = requests.get(status_check_url, headers=headers)
                            job_status_response.raise_for_status()
                            job_status_data = job_status_response.json()
                            current_job_status = job_status_data['data']['status']
                            print(f"DEBUG_LOG (Simulador_PJ.py): Status job CloudConvert '{job_id}': {current_job_status}")
                            
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
                                # ... (lógica de extração de erro) ...
                                st.error(f"Erro na conversão PDF via CloudConvert.")
                                break 
                            time.sleep(4) 
                        
                        if pdf_download_url:
                            pdf_file_content = requests.get(pdf_download_url).content 
                            st.download_button(
                                label="📥 Baixar Proposta em PDF",
                                data=pdf_file_content,
                                file_name=f"Proposta_Verdio_{nome_empresa.replace(' ', '_')}_{validade_proposta_dt.strftime('%Y%m%d')}.pdf",
                                mime="application/pdf",
                                key="pj_download_pdf_btn_v12_final_cc" 
                            )
                        elif final_job_status != 'error': 
                            st.error("Não foi possível obter o PDF ou tempo de espera excedido.")


            except FileNotFoundError:
                st.error(f"ERRO: Template DOCX '{doc_template_path}' não encontrado.")
            except requests.exceptions.RequestException as req_e:
                st.error(f"Erro de comunicação com CloudConvert: {req_e}")
            except Exception as e_gerar_pdf:
                st.error(f"Erro inesperado ao gerar proposta PDF: {e_gerar_pdf}")
                print(f"ERROR_LOG (Simulador_PJ.py): Erro na geração PDF: {type(e_gerar_pdf).__name__} - {e_gerar_pdf}")
    
elif not api_key_presente and produtos_selecionados_pj: 
    pass 
elif not produtos_selecionados_pj: 
    st.info("Selecione produtos para preencher dados e gerar uma proposta.")

print("INFO_LOG (Simulador_PJ.py): Renderização da página PJ concluída.")