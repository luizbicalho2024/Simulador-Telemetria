# pages/🤖_Automação_Cadastro.py
import streamlit as st
import pandas as pd
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import user_management_db as umdb

# --- 1. CONFIGURAÇÃO E AUTENTICAÇÃO ---
st.set_page_config(
    layout="wide",
    page_title="Automação de Cadastros",
    page_icon="🤖"
)

if not st.session_state.get("authentication_status"):
    st.error("🔒 Acesso Negado! Por favor, faça login para visualizar esta página.")
    st.stop()

# --- 2. CONSTANTES E SELETORES (CORRIGIDOS) ---
URL_DO_SISTEMA = "https://sistema.etrac.com.br/"
URL_BASE_CADASTRO_VEICULO = "https://sistema.etrac.com.br/index.php?r=veiculo%2Fcreate&id="
ID_CAMPO_USUARIO = "loginform-username"
ID_CAMPO_SENHA = "loginform-password"
BOTAO_ENTRAR_XPATH = "//button[@name='login-button']"

# IDs dos campos do formulário CORRIGIDOS de acordo com o código-fonte
INPUT_PLACA_ID = "input_veic_placa"
INPUT_CHASSI_ID = "veiculo-veic_chassi"
INPUT_MARCA_ID = "veiculo-veic_fabricante"
INPUT_MODELO_ID = "veiculo-veic_modelo"
INPUT_ANO_FABRICACAO_ID = "veiculo-veic_ano"
INPUT_ANO_MODELO_ID = "veiculo-veic_ano_modelo"
INPUT_COR_ID = "veiculo-veic_cor"
RADIO_PLACA_MERCOSUL_XPATH = "//input[@name='tipo_placa' and @value='2']"
BOTAO_CADASTRAR_VEICULO_XPATH = "//div[@class='form-group align-right']//button[contains(text(), 'Cadastrar')]"

COLUNAS_OBRIGATORIAS = [
    'ID_cliente', 'Segmento', 'Placa', 'Chassi', 'Marca', 'Modelo', 
    'Ano Modelo', 'Ano de Fabricação', 'Combustível', 'Cor', 
    'Origem de Veículo', 'Tanque de Combustivel', 'Mes Licenciamento'
]

# --- 3. FUNÇÃO PRINCIPAL DA AUTOMAÇÃO (CORRIGIDA) ---
def iniciar_automacao(username, password, df_veiculos, status_container):
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    
    summary = {'success': [], 'failed': []}
    driver = None

    try:
        service = Service() 
        driver = webdriver.Chrome(service=service, options=options)
        wait = WebDriverWait(driver, 30)
        
        status_container.info("1. A fazer login no sistema Etrac...")
        driver.get(URL_DO_SISTEMA)
        wait.until(EC.presence_of_element_located((By.ID, ID_CAMPO_USUARIO))).send_keys(username)
        driver.find_element(By.ID, ID_CAMPO_SENHA).send_keys(password)
        driver.find_element(By.XPATH, BOTAO_ENTRAR_XPATH).click()
        
        wait.until(EC.url_contains("index.php?r=site%2Findex"))
        status_container.success("   Login realizado com sucesso!")

        for id_cliente, group in df_veiculos.groupby('ID_cliente'):
            url_cadastro = f"{URL_BASE_CADASTRO_VEICULO}{id_cliente}"
            
            for index, veiculo in group.iterrows():
                placa = veiculo.get('Placa')
                with st.status(f"Processando veículo: **{placa}**...") as status:
                    try:
                        st.write(f"   - Navegando para a página de cadastro do cliente {id_cliente}...")
                        driver.get(url_cadastro)
                        
                        st.write("   - Aguardando formulário e preenchendo campos...")
                        placa_field = wait.until(EC.visibility_of_element_located((By.ID, INPUT_PLACA_ID)))
                        
                        placa_field.send_keys(placa)
                        driver.find_element(By.ID, INPUT_CHASSI_ID).send_keys(str(veiculo.get('Chassi', '')))
                        driver.find_element(By.ID, INPUT_MARCA_ID).send_keys(veiculo.get('Marca', ''))
                        driver.find_element(By.ID, INPUT_MODELO_ID).send_keys(veiculo.get('Modelo', ''))
                        driver.find_element(By.ID, INPUT_ANO_FABRICACAO_ID).send_keys(str(veiculo.get('Ano de Fabricação', '')))
                        driver.find_element(By.ID, INPUT_ANO_MODELO_ID).send_keys(str(veiculo.get('Ano Modelo', '')))
                        driver.find_element(By.ID, INPUT_COR_ID).send_keys(veiculo.get('Cor', ''))
                        
                        st.write("   - Selecionando Placa Mercosul...")
                        driver.find_element(By.XPATH, RADIO_PLACA_MERCOSUL_XPATH).click()
                        
                        st.write("   - Enviando o formulário...")
                        wait.until(EC.element_to_be_clickable((By.XPATH, BOTAO_CADASTRAR_VEICULO_XPATH))).click()
                        
                        # Confirma que o cadastro foi bem sucedido esperando a URL de sucesso (que é a mesma)
                        # e que o formulário está pronto para um novo cadastro (verificando o campo placa)
                        wait.until(EC.visibility_of_element_located((By.ID, INPUT_PLACA_ID)))
                        
                        summary['success'].append(placa)
                        status.update(label=f"Veículo **{placa}** cadastrado com sucesso!", state="complete")

                    except (TimeoutException, NoSuchElementException) as e:
                        error_msg = f"Falha ao cadastrar **{placa}**. O robô não encontrou um elemento ou a página demorou muito a responder."
                        st.error(error_msg)
                        summary['failed'].append({'placa': placa, 'motivo': 'Elemento não encontrado ou tempo de espera excedido'})
                        status.update(label=error_msg, state="error")
                        continue

    except Exception as e:
        st.error(f"Ocorreu um erro geral na automação: {e}")
        summary['failed'].append({'placa': 'GERAL', 'motivo': str(e)})
    finally:
        if driver:
            driver.quit()
        return summary

# --- 4. INTERFACE DA PÁGINA ---
st.markdown("<h1 style='text-align: center; color: #54A033;'>🤖 Automação de Cadastro de Veículos</h1>", unsafe_allow_html=True)
st.markdown("---")
st.info("Esta ferramenta automatiza o cadastro de múltiplos veículos no sistema Etrac a partir de uma planilha. Siga os passos abaixo.")
st.subheader("1. Credenciais de Acesso ao Sistema Etrac")
col1, col2 = st.columns(2)
etrac_user = col1.text_input("Usuário Etrac", key="etrac_user")
etrac_pass = col2.text_input("Senha Etrac", type="password", key="etrac_pass")
st.subheader("2. Upload da Planilha de Veículos")
uploaded_file = st.file_uploader("Carregue o arquivo `modelo_importacao.xlsx`", type=['xlsx'])
st.markdown("---")

if st.button("🚀 Iniciar Automação", use_container_width=True, type="primary"):
    if not etrac_user or not etrac_pass:
        st.error("Por favor, insira o seu utilizador e senha do sistema Etrac.")
    elif uploaded_file is None:
        st.error("Por favor, carregue a planilha de importação.")
    else:
        try:
            df = pd.read_excel(uploaded_file, header=1, engine='openpyxl')
            df.columns = df.columns.str.replace(r'\s*\(\*\)', '', regex=True).str.strip()

            st.write("🔍 A validar a planilha...")
            missing_cols = [col for col in COLUNAS_OBRIGATORIAS if col not in df.columns]
            
            if missing_cols:
                st.error(f"A planilha está em falta das seguintes colunas obrigatórias: **{', '.join(missing_cols)}**")
            else:
                df_obrigatorias = df[COLUNAS_OBRIGATORIAS].dropna(how='all')
                if df_obrigatorias.isnull().values.any():
                    st.error("A sua planilha tem células vazias em colunas obrigatórias. Por favor, preencha todos os campos e tente novamente.")
                else:
                    st.success("✅ Planilha validada com sucesso! A iniciar a automação...")
                    status_container = st.empty()
                    summary_report = iniciar_automacao(etrac_user, etrac_pass, df_obrigatorias, status_container)
                    
                    st.markdown("---")
                    st.subheader("🏁 Relatório Final da Automação")
                    st.metric("Total de Veículos Processados", len(summary_report['success']) + len(summary_report['failed']))
                    st.metric("✅ Sucessos", len(summary_report['success']))
                    st.metric("❌ Falhas", len(summary_report['failed']))

                    if summary_report['failed']:
                        st.error("Alguns veículos falharam ao serem cadastrados:")
                        for item in summary_report['failed']:
                            st.write(f"- **Placa:** {item['placa']} | **Motivo:** {item['motivo']}")
        except Exception as e:
            st.error(f"Não foi possível ler o ficheiro Excel. Verifique se o formato está correto. Detalhe do erro: {e}")
