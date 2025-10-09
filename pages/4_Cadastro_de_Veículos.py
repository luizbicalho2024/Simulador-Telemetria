# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import time
import os
from selenium import webdriver
# --- Alteração 1: Importar 'Options' do Selenium ---
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

# ==============================================================================
# FUNÇÃO PRINCIPAL DA AUTOMAÇÃO (COM CORREÇÃO PARA AMBIENTE SEM TELA)
# ==============================================================================
def executar_cadastro_veiculos(df, usuario, senha, progress_bar, status_text):
    """
    Executa a automação de cadastro de veículos a partir de um DataFrame.
    """
    # --- ETAPA 1: CONFIGURAÇÕES E SELETORES ---
    URL_DO_SISTEMA = "https://sistema.etrac.com.br/"
    URL_BASE_CADASTRO_VEICULO = "https://sistema.etrac.com.br/index.php?r=veiculo%2Fcreate&id="
    ID_CAMPO_USUARIO = "loginform-username"
    ID_CAMPO_SENHA = "loginform-password"
    BOTAO_ENTRAR_XPATH = "//button[@name='login-button']"
    RADIO_PLACA_MERCOSUL_XPATH = "//input[@name='tipo_placa' and @value='2']"
    SELECT2_TIPO_VEICULO_BOX_XPATH = "//span[@aria-labelledby='select2-veiculo-veti_codigo-container']"
    INPUT_PLACA_ID = "input_veic_placa"
    INPUT_CHASSI_ID = "veiculo-veic_chassi"
    INPUT_RENAVAM_ID = "veiculo-veic_renavam"
    INPUT_ANO_ID = "veiculo-veic_ano"
    INPUT_AUTONOMIA_ID = "veiculo-veic_autonomia_fabrica"
    INPUT_FABRICANTE_ID = "veiculo-veic_fabricante"
    INPUT_MODELO_ID = "veiculo-veic_modelo"
    INPUT_ANO_MODELO_ID = "veiculo-veic_ano_modelo"
    INPUT_COR_ID = "veiculo-veic_cor"
    INPUT_TANQUE_ID = "veiculo-veic_tanque_total"
    INPUT_MES_LICENCIAMENTO_ID = "veiculo-mes_licenciamento"
    BOTAO_CADASTRAR_VEICULO_XPATH = "//div[@class='form-group align-right']//button[contains(text(), 'Cadastrar')]"

    mapa_colunas = {
        'ID_cliente (*)': 'cliente_id', 'Cliente/Unidade': 'Nome do Cliente',
        'Segmento (*)': 'Segmento', 'Placa (*)': 'Placa', 'Chassi (*)': 'Chassis',
        'Renavam': 'Renavam', 'Ano de Fabricação (*)': 'Ano',
        'Autonomia': 'Autonomia', 'Marca (*)': 'Marca', 'Modelo (*)': 'Modelo',
        'Ano Modelo (*)': 'Ano Modelo', 'Cor (*)': 'Cor',
        'Tanque de Combustivel (*)': 'Tanque de Comb',
        'Mes Licenciamento (*)': 'Mes de Licenciamento'
    }
    df_renomeado = df.rename(columns=mapa_colunas)
    lista_de_clientes = df_renomeado.to_dict('records')

    # ##############################################################################
    # CORREÇÃO APLICADA AQUI: Configurações para rodar no Streamlit Cloud
    # ##############################################################################
    status_text.info("Configurando o navegador para ambiente de nuvem...")
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Roda o Chrome sem abrir uma janela
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    # ##############################################################################

    service = Service(ChromeDriverManager().install())
    # --- Alteração 2: Passar as 'options' na inicialização ---
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    # Não precisa mais maximizar a janela, pois não há janela
    # driver.maximize_window()
    
    wait = WebDriverWait(driver, 30)
    total_veiculos = len(lista_de_clientes)

    try:
        status_text.info("1/3 - Acessando o sistema e realizando login...")
        driver.get(URL_DO_SISTEMA)
        
        wait.until(EC.presence_of_element_located((By.ID, ID_CAMPO_USUARIO))).send_keys(usuario)
        wait.until(EC.presence_of_element_located((By.ID, ID_CAMPO_SENHA))).send_keys(senha)
        wait.until(EC.element_to_be_clickable((By.XPATH, BOTAO_ENTRAR_XPATH))).click()
        
        status_text.info("Login realizado com sucesso. Aguardando a página principal...")
        time.sleep(5)

        status_text.info("2/3 - Iniciando o cadastro dos veículos...")
        for i, cliente in enumerate(lista_de_clientes):
            progresso = (i + 1) / total_veiculos
            progress_bar.progress(progresso)
            
            nome_cliente = cliente.get('Nome do Cliente', 'N/A')
            cliente_id = cliente.get('cliente_id')
            placa_veiculo = cliente.get('Placa', 'N/A')
            
            status_text.info(f"Cadastrando veículo {i+1}/{total_veiculos} (Placa: {placa_veiculo})...")

            if not cliente_id:
                st.warning(f"Registro para '{nome_cliente}' não possui 'ID_cliente'. Pulando...")
                continue
            
            try:
                url_final = f"{URL_BASE_CADASTRO_VEICULO}{cliente_id}"
                driver.get(url_final)

                radio_mercosul = wait.until(EC.presence_of_element_located((By.XPATH, RADIO_PLACA_MERCOSUL_XPATH)))
                driver.execute_script("arguments[0].click();", radio_mercosul)
                time.sleep(1)

                segmento_veiculo = str(cliente.get('Segmento', 'Outros')).capitalize()
                wait.until(EC.element_to_be_clickable((By.XPATH, SELECT2_TIPO_VEICULO_BOX_XPATH))).click()
                xpath_opcao_veiculo = f"//span[@class='select2-results']//li[text()='{segmento_veiculo}']"
                wait.until(EC.element_to_be_clickable((By.XPATH, xpath_opcao_veiculo))).click()
                
                driver.find_element(By.ID, INPUT_PLACA_ID).send_keys(str(cliente.get('Placa', '')))
                driver.find_element(By.ID, INPUT_CHASSI_ID).send_keys(str(cliente.get('Chassis', '')))
                driver.find_element(By.ID, INPUT_RENAVAM_ID).send_keys(str(cliente.get('Renavam', '')))
                driver.find_element(By.ID, INPUT_ANO_ID).send_keys(str(cliente.get('Ano', '')))
                driver.find_element(By.ID, INPUT_AUTONOMIA_ID).send_keys(str(cliente.get('Autonomia', '0')))
                driver.find_element(By.ID, INPUT_FABRICANTE_ID).send_keys(str(cliente.get('Marca', '')))
                driver.find_element(By.ID, INPUT_MODELO_ID).send_keys(str(cliente.get('Modelo', '')))
                driver.find_element(By.ID, INPUT_ANO_MODELO_ID).send_keys(str(cliente.get('Ano Modelo', '')))
                driver.find_element(By.ID, INPUT_COR_ID).send_keys(str(cliente.get('Cor', '')))
                driver.find_element(By.ID, INPUT_TANQUE_ID).send_keys(str(cliente.get('Tanque de Comb', '')))
                driver.find_element(By.ID, INPUT_MES_LICENCIAMENTO_ID).send_keys(str(int(cliente.get('Mes de Licenciamento', ''))))

                wait.until(EC.element_to_be_clickable((By.XPATH, BOTAO_CADASTRAR_VEICULO_XPATH))).click()
                
                st.write(f"✅ Sucesso: Veículo '{placa_veiculo}' cadastrado para '{nome_cliente}'.")
                time.sleep(2)

            except (TimeoutException, NoSuchElementException) as e:
                st.error(f"❌ Erro ao cadastrar '{placa_veiculo}'. Pulando para o próximo.")
                st.error(f"   Detalhe: Verifique se o 'Segmento' ({segmento_veiculo}) está correto ou se o veículo já existe.")
                continue
        
        status_text.success("3/3 - Processo de automação finalizado!")
        return True

    except Exception as e:
        status_text.error(f"‼️ OCORREU UM ERRO GERAL NO SCRIPT ‼️")
        st.error(f"Mensagem de erro: {e}")
        try:
            # Em modo headless, o screenshot ainda é útil para depuração
            driver.save_screenshot("erro_geral_automacao.png")
            st.image("erro_geral_automacao.png")
        except:
            st.error("Não foi possível capturar a tela do erro.")
        return False
    
    finally:
        if 'driver' in locals():
            driver.quit()

# ==============================================================================
# INTERFACE DO USUÁRIO COM STREAMLIT (Sem alterações aqui)
# ==============================================================================
st.set_page_config(page_title="Automação de Cadastro de Veículos", layout="wide")

st.title("🤖 Automação de Cadastro de Veículos")

st.markdown("""
Esta página permite cadastrar múltiplos veículos no sistema de forma automática.
Siga os passos abaixo:
1.  **Baixe o modelo**: Se ainda não tiver, use o link para baixar o modelo de importação.
2.  **Carregue o arquivo**: Preencha o modelo e carregue o arquivo CSV ou Excel.
3.  **Insira suas credenciais**: Digite seu usuário e senha do sistema.
4.  **Inicie a automação**: Clique no botão e aguarde o processo ser concluído.
""")

try:
    script_dir = os.path.dirname(__file__) 
    model_file_path = os.path.join(script_dir, '..', 'modelo_importacao - Sheet1.csv')

    with open(model_file_path, "rb") as file:
        st.download_button(
            label="📄 Baixar Modelo de Importação (CSV)",
            data=file,
            file_name="modelo_importacao.csv",
            mime="text/csv",
        )
except FileNotFoundError:
    st.warning("Arquivo 'modelo_importacao - Sheet1.csv' não encontrado. O botão de download está desativado.")

st.divider()

uploaded_file = st.file_uploader(
    "Carregue o arquivo de veículos (CSV ou Excel)",
    type=["csv", "xlsx"]
)

if uploaded_file:
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file, skiprows=1)
        else:
            df = pd.read_excel(uploaded_file, skiprows=1)
        
        df.dropna(subset=['ID_cliente (*)'], inplace=True)
        df['ID_cliente (*)'] = df['ID_cliente (*)'].astype(int)

        st.success("Arquivo carregado e processado com sucesso!")
        st.dataframe(df)

        st.divider()

        st.subheader("Credenciais do Sistema")
        col1, col2 = st.columns(2)
        with col1:
            usuario = st.text_input("Usuário", placeholder="seu.email@dominio.com")
        with col2:
            senha = st.text_input("Senha", type="password", placeholder="Sua senha de acesso")

        if st.button("🚀 Iniciar Cadastro em Lote", type="primary", use_container_width=True):
            if not usuario or not senha:
                st.error("Por favor, insira o usuário e a senha para continuar.")
            elif df.empty:
                st.error("O arquivo carregado está vazio ou não contém dados válidos.")
            else:
                st.info("Iniciando a automação... Este processo ocorre em segundo plano e pode levar alguns minutos.")
                
                progress_bar = st.progress(0)
                status_text = st.empty()

                sucesso = executar_cadastro_veiculos(df, usuario, senha, progress_bar, status_text)

                if sucesso:
                    st.balloons()

    except Exception as e:
        st.error(f"Ocorreu um erro ao processar o arquivo: {e}")
