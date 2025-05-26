# pages/Simulador_PJ.py
# Importações Python padrão primeiro
from io import BytesIO
from docx import Document # Para python-docx, certifique-se que é 'python-docx' no requirements.txt
from docx.shared import Pt
import requests
import time
from datetime import datetime
# A importação de Decimal não estava no seu script PJ, mas se você fizer cálculos financeiros, considere:
# from decimal import Decimal, ROUND_DOWN 
from decimal import Decimal, ROUND_DOWN
import streamlit as st

# 1. st.set_page_config() - PRIMEIRO COMANDO STREAMLIT
st.set_page_config(
    layout="wide",
    page_title="Simulador Pessoa Jurídica", # Título da aba específico
    page_icon="imgs/v-c.png", # Verifique se o caminho para a imagem do ícone está correto
    initial_sidebar_state="expanded"
)

# 2. BLOCO DE VERIFICAÇÃO DE AUTENTICAÇÃO
auth_status = st.session_state.get("authentication_status", False)
if auth_status is not True:
    st.error("🔒 Acesso Negado! Por favor, faça login na página principal para continuar.")
    print(f"ACCESS_DENIED_LOG (Simulador_PJ.py): User not authenticated. Status: {auth_status}")
    try:
        # Certifique-se que o nome do arquivo da página principal está correto aqui
        st.page_link("Simulador_Comercial.py", label="Ir para Login", icon="🏠")
    except AttributeError: 
        st.info("Retorne à página principal para efetuar o login.")
    st.stop() 

# Se chegou aqui, o usuário está autenticado.
current_username = st.session_state.get('username', 'N/A')
current_role = st.session_state.get('role', 'Indefinido') 
current_name = st.session_state.get('name', 'N/A')

print(f"INFO_LOG (Simulador_PJ.py): User '{current_username}' authenticated. Role: '{current_role}'")

# 3. Restante do código da sua página - AGORA o conteúdo da página começa

# 🛡️ Token CloudConvert - Idealmente, pegue de st.secrets no Streamlit Cloud
API_KEY_CLOUDCONVERT = st.secrets.get("CLOUDCONVERT_API_KEY") # Exemplo: st.secrets["CLOUDCONVERT_API_KEY"]
if not API_KEY_CLOUDCONVERT:
    # Se a API Key for essencial e não estiver configurada, avise ou pare.
    # Para este exemplo, vamos apenas avisar e permitir que a página continue sem a funcionalidade de PDF.
    print("WARN_LOG (Simulador_PJ.py): CLOUDCONVERT_API_KEY não configurada nos segredos. Geração de PDF desativada.")
    # st.warning("API Key do CloudConvert não configurada. Geração de PDF pode não funcionar.")

# 🔵 Logotipo e cabeçalho estilizado
try:
    st.image("imgs/logo.png", width=250) # Verifique o caminho
except FileNotFoundError:
    print("WARN_LOG (Simulador_PJ.py): Arquivo imgs/logo.png não encontrado.")
except Exception as e_img:
    print(f"WARN_LOG (Simulador_PJ.py): Erro ao carregar imgs/logo.png: {e_img}")

st.markdown("<h1 style='text-align: center; color: #54A033;'>Simulador de Venda - Pessoa Jurídica</h1>", unsafe_allow_html=True)
st.markdown("---")

# Informações do usuário logado (após o cabeçalho principal da página)
st.write(f"Usuário: {current_name} ({current_username})")
st.write(f"Nível de Acesso: {current_role}") 
st.markdown("---")

# Produtos (usando Decimal para os preços para precisão financeira)
planos = {
    "12 Meses": {
        "GPRS / Gsm": Decimal("80.88"),
        "Satélite": Decimal("193.80"),
        "Identificador de Motorista / RFID": Decimal("19.25"),
        "Leitor de Rede CAN / Telemetria": Decimal("75.25"),
        "Videomonitoramento + DMS + ADAS": Decimal("409.11")
    },
    "24 Meses": {
        "GPRS / Gsm": Decimal("53.92"),
        "Satélite": Decimal("129.20"),
        "Identificador de Motorista / RFID": Decimal("12.83"),
        "Leitor de Rede CAN / Telemetria": Decimal("50.17"),
        "Videomonitoramento + DMS + ADAS": Decimal("272.74")
    },
    "36 Meses": {
        "GPRS / Gsm": Decimal("44.93"),
        "Satélite": Decimal("107.67"),
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
st.sidebar.header("📝 Configurações PJ") # Título mais específico
# Chaves únicas para widgets da sidebar
qtd_veiculos_key = "pj_qtd_veiculos_sb"
temp_contrato_key = "pj_temp_contrato_sb"

qtd_veiculos = st.sidebar.number_input("Quantidade de Veículos 🚗", min_value=1, value=1, key=qtd_veiculos_key)
temp_contrato_selecionado = st.sidebar.selectbox("Tempo de Contrato ⏳", list(planos.keys()), key=temp_contrato_key)

# Seção principal
st.markdown("### 🛠️ Selecione os Produtos:")
col1_pj, col2_pj = st.columns(2) # Renomeadas para evitar conflitos
produtos_selecionados_pj = {} # Dicionário para armazenar produtos e seus preços

# Loop para criar os toggles com chaves únicas
for i, (produto, preco) in enumerate(planos[temp_contrato_selecionado].items()):
    col_target = col1_pj if i % 2 == 0 else col2_pj
    # Chave única para cada toggle
    produto_toggle_key = f"pj_toggle_{produto.replace(' ', '_').replace('/', '_')}"
    if col_target.toggle(f"{produto} - R$ {preco:,.2f}", key=produto_toggle_key):
        produtos_selecionados_pj[produto] = preco # Armazena o Decimal

# Cálculos
soma_mensal_produtos_selecionados = sum(produtos_selecionados_pj.values()) # Soma de Decimals
valor_mensal_total_frota = soma_mensal_produtos_selecionados * Decimal(str(qtd_veiculos)) # Multiplicação de Decimals
# O tempo de contrato já está em meses (ex: "12 Meses", "24 Meses")
meses_contrato = Decimal(temp_contrato_selecionado.split()[0]) 
valor_total_contrato = valor_mensal_total_frota * meses_contrato

st.markdown("---")
if produtos_selecionados_pj: # Só mostra resultados se algo foi selecionado
    st.success(f"✅ Valor Mensal por Veículo (soma dos produtos): R$ {soma_mensal_produtos_selecionados:,.2f}")
    st.info(f"💰 Valor Mensal Total para a Frota ({qtd_veiculos} veíc.): R$ {valor_mensal_total_frota:,.2f}")
    st.info(f"📄 Valor Total do Contrato ({temp_contrato_selecionado}): R$ {valor_total_contrato:,.2f}")
else:
    st.info("Selecione produtos para ver o cálculo.")


if st.button("🔄 Limpar Seleção e Recalcular", key="pj_btn_limpar_recalcular"):
    st.rerun()

# Formulário para Gerar Proposta
if produtos_selecionados_pj and API_KEY_CLOUDCONVERT: # Só mostra se há produtos e API Key
    st.markdown("---")
    st.subheader("📄 Gerar Proposta em PDF")

    with st.form("formulario_proposta_pj", key="pj_form_proposta"): # Chave única para o formulário
        # Chaves únicas para os inputs do formulário
        nome_empresa = st.text_input("Nome da Empresa", key="pj_form_nome_empresa")
        nome_responsavel = st.text_input("Nome do Responsável", key="pj_form_nome_responsavel")
        nome_consultor = st.text_input("Nome do Consultor Comercial", key="pj_form_nome_consultor")
        validade_proposta_dt = st.date_input("Validade da Proposta", value=datetime.today(), key="pj_form_validade_proposta")
        
        gerar_proposta_btn = st.form_submit_button("Gerar Proposta")

    if gerar_proposta_btn:
        print(f"INFO_LOG (Simulador_PJ.py): Botão 'Gerar Proposta' clicado. Empresa: {nome_empresa}")
        if not all([nome_empresa, nome_responsavel, nome_consultor]):
            st.warning("Por favor, preencha todos os dados da proposta (Empresa, Responsável, Consultor).")
        else:
            try:
                # Caminho para o template DOCX - deve estar na raiz do projeto ou um caminho acessível
                # Se estiver na pasta 'pages', o caminho seria "pages/Proposta Comercial e Intenção - Verdio.docx"
                # Mas geralmente templates ficam na raiz ou em uma pasta 'templates'.
                # Para o Streamlit Cloud, o caminho é relativo à raiz do repositório.
                # Assumindo que "Proposta Comercial e Intenção - Verdio.docx" está na raiz.
                doc_template_path = "Proposta Comercial e Intenção - Verdio.docx"
                doc = Document(doc_template_path) #
                print(f"INFO_LOG (Simulador_PJ.py): Template DOCX '{doc_template_path}' carregado.")

                # Substituições no texto
                for p in doc.paragraphs:
                    if "Nome da empresa" in p.text: p.text = p.text.replace("Nome da empresa", nome_empresa)
                    if "Nome do Responsável" in p.text: p.text = p.text.replace("Nome do Responsável", nome_responsavel)
                    if "00/00/0000" in p.text: p.text = p.text.replace("00/00/0000", validade_proposta_dt.strftime("%d/%m/%Y"))
                    if "Nome do comercial" in p.text: p.text = p.text.replace("Nome do comercial", nome_consultor)

                # Substituições na tabela de produtos
                for table in doc.tables:
                    if any("Item" in cell.text for cell in table.rows[0].cells): # Identifica a tabela correta
                        # Limpa linhas antigas (exceto o cabeçalho)
                        while len(table.rows) > 1:
                            table._tbl.remove(table.rows[1]._tr)
                        
                        # Adiciona novos produtos selecionados
                        for produto_sel, preco_sel in produtos_selecionados_pj.items():
                            row_cells = table.add_row().cells
                            row_cells[0].text = produto_sel
                            row_cells[1].text = produtos_descricao.get(produto_sel, "Descrição não disponível") # Pega descrição
                            row_cells[2].text = f"R$ {preco_sel:,.2f}" # Preço mensal unitário
                        
                        # Adiciona linha de TOTAL MENSAL POR VEÍCULO
                        total_row = table.add_row().cells
                        total_row[0].text = "TOTAL MENSAL POR VEÍCULO"
                        total_row[0].paragraphs[0].runs[0].font.bold = True
                        total_row[1].text = "" 
                        total_row[2].text = f"R$ {soma_mensal_produtos_selecionados:,.2f}"
                        total_row[2].paragraphs[0].runs[0].font.bold = True
                        break # Sai do loop de tabelas após encontrar e preencher a tabela de itens

                buffer_docx = BytesIO()
                doc.save(buffer_docx)
                buffer_docx.seek(0)
                print("INFO_LOG (Simulador_PJ.py): DOCX da proposta gerado em buffer.")

                # Lógica de conversão para PDF com CloudConvert
                with st.spinner("Gerando PDF da proposta, aguarde..."):
                    headers = {"Authorization": f"Bearer {API_KEY_CLOUDCONVERT}"}
                    job_payload = {
                        "tasks": {
                            "import-1": {"operation": "import/upload"},
                            "convert-1": {"operation": "convert", "input": "import-1", "input_format": "docx", "output_format": "pdf", "engine": "libreoffice"},
                            "export-1": {"operation": "export/url", "input": "convert-1", "inline": False, "archive_multiple_files": False}
                        }
                    }
                    job_response = requests.post('https://api.cloudconvert.com/v2/jobs', json=job_payload, headers=headers)
                    job_response.raise_for_status() # Levanta erro HTTP se houver
                    job_data = job_response.json()
                    
                    upload_url = job_data['data']['tasks'][0]['result']['form']['url']
                    parameters = job_data['data']['tasks'][0]['result']['form']['parameters']
                    
                    files_payload = {'file': (f'proposta_{nome_empresa.replace(" ", "_")}.docx', buffer_docx, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')}
                    upload_response = requests.post(upload_url, data=parameters, files=files_payload)
                    upload_response.raise_for_status()
                    print(f"INFO_LOG (Simulador_PJ.py): DOCX enviado para CloudConvert. Status: {upload_response.status_code}")

                    job_id = job_data['data']['id']
                    status_check_url = f'https://api.cloudconvert.com/v2/jobs/{job_id}'
                    
                    # Esperar o processamento
                    max_wait_time = 120 # Segundos (2 minutos)
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
                                if task['name'] == 'export-1' and task.get('status') == 'finished':
                                    if task.get('result') and task['result'].get('files'):
                                        pdf_url = task['result']['files'][0]['url']
                                        break
                            break 
                        elif job_status == 'error':
                            st.error(f"Erro na conversão para PDF: {check_data['data'].get('message', 'Erro desconhecido do CloudConvert')}")
                            print(f"ERROR_LOG (Simulador_PJ.py): Erro no job CloudConvert '{job_id}': {check_data['data']}")
                            break
                        time.sleep(3) # Espera antes de verificar novamente
                    
                    if pdf_url:
                        print(f"INFO_LOG (Simulador_PJ.py): PDF gerado com sucesso. URL: {pdf_url}")
                        pdf_response = requests.get(pdf_url)
                        pdf_response.raise_for_status()
                        st.download_button(
                            label="📥 Baixar Proposta em PDF",
                            data=pdf_response.content,
                            file_name=f"Proposta_Verdio_{nome_empresa.replace(' ', '_')}.pdf",
                            mime="application/pdf",
                            key="pj_download_pdf_btn"
                        )
                    elif job_status != 'error': # Se não houve erro explícito, mas não obteve URL
                        st.error("Erro ao finalizar a exportação do PDF ou tempo de espera excedido.")
                        print(f"ERROR_LOG (Simulador_PJ.py): Job CloudConvert '{job_id}' finalizado sem URL de PDF ou timeout.")

            except FileNotFoundError:
                st.error(f"ERRO: O arquivo template '{doc_template_path}' não foi encontrado. Verifique o caminho.")
                print(f"ERROR_LOG (Simulador_PJ.py): Template DOCX '{doc_template_path}' não encontrado.")
            except requests.exceptions.RequestException as req_e:
                st.error(f"Erro de comunicação com o serviço CloudConvert: {req_e}")
                print(f"ERROR_LOG (Simulador_PJ.py): CloudConvert RequestException: {req_e}")
            except Exception as e_gerar:
                st.error(f"Ocorreu um erro ao gerar a proposta: {e_gerar}")
                print(f"ERROR_LOG (Simulador_PJ.py): Erro na geração da proposta: {e_gerar}")
elif API_KEY_CLOUDCONVERT is None and produtos_selecionados_pj:
    st.markdown("---")
    st.warning("⚠️ A funcionalidade de gerar proposta em PDF está desativada porque a chave da API do CloudConvert não está configurada nos segredos do aplicativo.")