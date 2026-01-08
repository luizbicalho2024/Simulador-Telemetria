# pages/4_Cadastro_de_Veículos.py
# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import time
import os
import io
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

# ==============================================================================
# FUNÇÃO PRINCIPAL DA AUTOMAÇÃO (VERSÃO DEBUG E ENVIO FORÇADO)
# ==============================================================================
def executar_cadastro_veiculos(df, usuario, senha, progress_bar, status_text):
    """
    Executa a automação de cadastro de veículos com captura de tela em caso de erro.
    """
    # --- CONFIGURAÇÕES ---
    URL_DO_SISTEMA = "https://sistema.etrac.com.br/"
    URL_BASE_CADASTRO_VEICULO = "https://sistema.etrac.com.br/index.php?r=veiculo%2Fcreate&id="
    
    # Seletores
    ID_CAMPO_USUARIO = "loginform-username"
    ID_CAMPO_SENHA = "loginform-password"
    BOTAO_ENTRAR_XPATH = "//button[@name='login-button']"
    
    # Seletores do Formulário
    FORM_ID = "veiculo" # ID do form no HTML
    RADIO_PLACA_MERCOSUL_XPATH = "//input[@name='tipo_placa' and @value='2']"
    SELECT2_TIPO_VEICULO_BOX_XPATH = "//span[@aria-labelledby='select2-veiculo-veti_codigo-container']"
    
    # Inputs
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
    
    # Botão Cadastrar
    BOTAO_CADASTRAR_VEICULO_XPATH = "//button[contains(text(), 'Cadastrar')]"
    
    # Mensagens
    MENSAGEM_SUCESSO_XPATH = "//div[contains(@class, 'alert-success')]"
    MENSAGEM_ERRO_GERAL_XPATH = "//div[contains(@class, 'alert-danger')]"
    MENSAGEM_ERRO_CAMPO_XPATH = "//div[contains(@class, 'has-error')]//div[contains(@class, 'help-block')]"

    # Mapeamento
    mapa_colunas = {
        'ID_cliente (*)': 'cliente_id', 'Cliente/Unidade': 'Nome do Cliente',
        'Segmento (*)': 'Segmento', 'Placa (*)': 'Placa', 'Chassi (*)': 'Chassis',
        'Renavam': 'Renavam', 'Ano de Fabricação (*)': 'Ano',
        'Autonomia': 'Autonomia', 'Marca (*)': 'Marca', 'Modelo (*)': 'Modelo',
        'Ano Modelo (*)': 'Ano Modelo', 'Cor  (*)': 'Cor',
        'Tanque de Combustivel (*)': 'Tanque de Comb',
        'Mes Licenciamento (*)': 'Mes de Licenciamento'
    }
    
    try:
        df_renomeado = df.rename(columns=mapa_colunas)
        lista_de_clientes = df_renomeado.to_dict('records')
    except Exception as e:
        st.error(f"Erro ao processar colunas. {e}")
        return False

    # Configuração Chrome
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080") # Tela grande para evitar sobreposição
    chrome_options.add_argument("--disk-cache-dir=/dev/null") # Evitar cache
    
    service = Service()
    
    try:
        driver = webdriver.Chrome(service=service, options=chrome_options)
    except Exception as e:
        st.error(f"Erro driver: {e}")
        return False
    
    wait = WebDriverWait(driver, 20)
    total_veiculos = len(lista_de_clientes)

    try:
        # LOGIN
        status_text.info("Acessando sistema...")
        driver.get(URL_DO_SISTEMA)
        wait.until(EC.presence_of_element_located((By.ID, ID_CAMPO_USUARIO))).send_keys(usuario)
        driver.find_element(By.ID, ID_CAMPO_SENHA).send_keys(senha)
        driver.find_element(By.XPATH, BOTAO_ENTRAR_XPATH).click()
        time.sleep(3)

        # LOOP DE CADASTRO
        for i, cliente in enumerate(lista_de_clientes):
            progresso = (i + 1) / total_veiculos
            progress_bar.progress(progresso)
            
            nome_cliente = cliente.get('Nome do Cliente', 'N/A')
            cliente_id = str(cliente.get('cliente_id', '')).replace('.0', '')
            placa_veiculo = cliente.get('Placa', 'N/A')

            status_text.info(f"Processando: {placa_veiculo}...")

            if not cliente_id or cliente_id == 'nan':
                continue
            
            try:
                # ACESSA URL DIRETA
                driver.get(f"{URL_BASE_CADASTRO_VEICULO}{cliente_id}")
                
                # Preenchimento (Lógica idêntica ao anterior)
                try:
                    radio = wait.until(EC.presence_of_element_located((By.XPATH, RADIO_PLACA_MERCOSUL_XPATH)))
                    driver.execute_script("arguments[0].click();", radio)
                except:
                    pass # Pode já estar selecionado ou não carregar a tempo

                # Segmento
                try:
                    segmento = str(cliente.get('Segmento', 'Outros')).capitalize()
                    wait.until(EC.element_to_be_clickable((By.XPATH, SELECT2_TIPO_VEICULO_BOX_XPATH))).click()
                    xpath_opt = f"//span[@class='select2-results']//li[text()='{segmento}']"
                    wait.until(EC.element_to_be_clickable((By.XPATH, xpath_opt))).click()
                except:
                    st.warning(f"Não foi possível selecionar segmento para {placa_veiculo}")

                # Campos Texto
                def fill(bid, val):
                    if val and str(val).lower() != 'nan':
                        e = driver.find_element(By.ID, bid)
                        e.clear()
                        e.send_keys(str(val).replace('.0', ''))

                fill(INPUT_PLACA_ID, placa_veiculo)
                fill(INPUT_CHASSI_ID, cliente.get('Chassis', ''))
                fill(INPUT_RENAVAM_ID, cliente.get('Renavam', ''))
                fill(INPUT_ANO_ID, cliente.get('Ano', ''))
                fill(INPUT_AUTONOMIA_ID, cliente.get('Autonomia', '0'))
                fill(INPUT_FABRICANTE_ID, cliente.get('Marca', ''))
                fill(INPUT_MODELO_ID, cliente.get('Modelo', ''))
                fill(INPUT_ANO_MODELO_ID, cliente.get('Ano Modelo', ''))
                fill(INPUT_COR_ID, cliente.get('Cor', ''))
                fill(INPUT_TANQUE_ID, cliente.get('Tanque de Comb', ''))
                fill(INPUT_MES_LICENCIAMENTO_ID, cliente.get('Mes de Licenciamento', ''))

                # --- TENTATIVA DE ENVIO ROBUSTA ---
                time.sleep(1)
                
                # Estratégia 1: Submit Direto no Form (Ignora botão visual)
                try:
                    form_element = driver.find_element(By.ID, FORM_ID)
                    driver.execute_script("arguments[0].submit();", form_element)
                except Exception as e_submit:
                    # Estratégia 2: Clique via JS no Botão
                    try:
                        btn = driver.find_element(By.XPATH, BOTAO_CADASTRAR_VEICULO_XPATH)
                        driver.execute_script("arguments[0].scrollIntoView(true);", btn)
                        time.sleep(0.5)
                        driver.execute_script("arguments[0].click();", btn)
                    except:
                        pass

                # Aguarda processamento
                time.sleep(3) 
                
                # --- VERIFICAÇÃO ---
                msg_sucesso = driver.find_elements(By.XPATH, MENSAGEM_SUCESSO_XPATH)
                msg_erro = driver.find_elements(By.XPATH, MENSAGEM_ERRO_GERAL_XPATH)
                msg_erro_campo = driver.find_elements(By.XPATH, MENSAGEM_ERRO_CAMPO_XPATH)

                if msg_sucesso:
                    st.write(f"✅ **{placa_veiculo}**: Cadastrado!")
                
                elif msg_erro or msg_erro_campo:
                    err_txt = msg_erro[0].text if msg_erro else "Erro em campo específico"
                    if msg_erro_campo:
                        err_txt += f" ({msg_erro_campo[0].text})"
                    st.error(f"❌ **{placa_veiculo}**: {err_txt}")
                    
                    # Screenshot do erro
                    driver.save_screenshot(f"erro_{placa_veiculo}.png")
                    st.image(f"erro_{placa_veiculo}.png", caption=f"Tela de Erro: {placa_veiculo}")
                
                else:
                    st.warning(f"⚠️ **{placa_veiculo}**: Sem confirmação. Verifique a imagem abaixo.")
                    # Screenshot do Mistério
                    driver.save_screenshot(f"misterio_{placa_veiculo}.png")
                    st.image(f"misterio_{placa_veiculo}.png", caption=f"Estado final da tela: {placa_veiculo}")

            except Exception as e:
                st.error(f"Erro crítico no loop: {e}")
                driver.save_screenshot("erro_critico.png")
                st.image("erro_critico.png")
                continue
        
        status_text.success("Finalizado!")
        return True

    except Exception as e:
        st.error(f"Erro Geral: {e}")
        return False
    finally:
        if 'driver' in locals():
            driver.quit()

# ==============================================================================
# INTERFACE
# ==============================================================================
st.set_page_config(page_title="Automação Veículos", layout="wide")
st.title("🤖 Automação de Cadastro de Veículos (Modo Debug)")

# (Mantém a lógica de download do modelo igual ao anterior, omitido para brevidade)
try:
    script_dir = os.path.dirname(__file__) 
    model_file_path = os.path.join(script_dir, '..', 'modelo_importacao - Sheet1.csv')
    if not os.path.exists(model_file_path): model_file_path = 'modelo_importacao - Sheet1.csv'
    if os.path.exists(model_file_path):
        df_modelo = pd.read_csv(model_file_path)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_modelo.to_excel(writer, index=False, sheet_name='Sheet1')
        st.download_button("📄 Baixar Modelo XLSX", data=output.getvalue(), file_name="modelo_importacao.xlsx")
except: pass

uploaded_file = st.file_uploader("Carregue o arquivo", type=["csv", "xlsx"])

if uploaded_file:
    try:
        if uploaded_file.name.endswith('.csv'): df = pd.read_csv(uploaded_file, skiprows=1)
        else: df = pd.read_excel(uploaded_file, skiprows=1)
        
        if 'ID_cliente (*)' in df.columns:
            df.dropna(subset=['ID_cliente (*)'], inplace=True)
        
        st.success(f"Arquivo carregado! {len(df)} veículos encontrados.")
        
        c1, c2 = st.columns(2)
        usuario = c1.text_input("Usuário")
        senha = c2.text_input("Senha", type="password")

        if st.button("🚀 Iniciar com Diagnóstico de Tela", type="primary"):
            if usuario and senha:
                executar_cadastro_veiculos(df, usuario, senha, st.progress(0), st.empty())
            else:
                st.error("Preencha usuário e senha.")
    except Exception as e:
        st.error(f"Erro arquivo: {e}")
