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
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

# ==============================================================================
# FUNÇÕES AUXILIARES AVANÇADAS
# ==============================================================================
def input_force_js(driver, element_id, value):
    """
    Força a inserção do valor via JavaScript e dispara eventos de validação.
    Isso resolve problemas com máscaras (InputMask) e validações do Yii Framework.
    """
    if value and str(value).lower() != 'nan':
        value = str(value).replace('.0', '').strip()
        try:
            element = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, element_id)))
            
            # Rola até o elemento
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
            
            # 1. Limpa e Digita (Método Tradicional)
            try:
                element.click()
                element.send_keys(Keys.CONTROL + "a")
                element.send_keys(Keys.DELETE)
                element.send_keys(value)
            except: pass

            # 2. Força Bruta via JS (Garante que o valor fique)
            driver.execute_script("arguments[0].value = arguments[1];", element, value)
            
            # 3. Dispara Eventos de Validação (O segredo para o sistema aceitar)
            driver.execute_script("arguments[0].dispatchEvent(new Event('input', { bubbles: true }));", element)
            driver.execute_script("arguments[0].dispatchEvent(new Event('change', { bubbles: true }));", element)
            driver.execute_script("arguments[0].dispatchEvent(new Event('blur', { bubbles: true }));", element)
            
        except Exception as e:
            print(f"Erro ao preencher {element_id}: {e}")

def tentar_selecionar_contrato(driver):
    """
    Tenta selecionar o primeiro contrato disponível se o campo estiver vazio.
    O novo formulário exige isso, mesmo que pareça opcional.
    """
    try:
        # Verifica se o Select2 do contrato está visível
        SELECT2_CONTRATO = "//span[@aria-labelledby='select2-veiculo-contrato_vinculo_veiculo-container']"
        if driver.find_elements(By.XPATH, SELECT2_CONTRATO):
            driver.find_element(By.XPATH, SELECT2_CONTRATO).click()
            time.sleep(0.5)
            # Seleciona a primeira opção válida que aparecer (geralmente o contrato padrão)
            # O xpath pega o primeiro 'li' que é uma opção selecionável
            OPCAO_CONTRATO = "//li[contains(@class, 'select2-results__option') and not(contains(@class, 'loading'))]"
            opcoes = WebDriverWait(driver, 2).until(EC.presence_of_all_elements_located((By.XPATH, OPCAO_CONTRATO)))
            
            if opcoes:
                # Clica no segundo item (o primeiro costuma ser "Selecione...") ou no primeiro disponível
                if len(opcoes) > 1:
                    opcoes[1].click() 
                else:
                    opcoes[0].click()
    except:
        pass # Se der erro ou não tiver contrato, segue vida

# ==============================================================================
# FUNÇÃO PRINCIPAL
# ==============================================================================
def executar_cadastro_veiculos(df, usuario, senha, progress_bar, status_text):
    # --- CONFIGURAÇÕES ---
    URL_DO_SISTEMA = "https://sistema.etrac.com.br/"
    URL_BASE_CADASTRO_VEICULO = "https://sistema.etrac.com.br/index.php?r=veiculo%2Fcreate&id="
    
    # IDs e XPaths
    ID_USUARIO = "loginform-username"
    ID_SENHA = "loginform-password"
    BTN_LOGIN = "//button[@name='login-button']"
    RADIO_MERCOSUL = "//input[@name='tipo_placa' and @value='2']"
    SELECT2_SEGMENTO = "//span[@aria-labelledby='select2-veiculo-veti_codigo-container']"
    BTN_CADASTRAR = "//button[contains(text(), 'Cadastrar')]"
    
    # Mensagens de Retorno
    MSG_SUCESSO = "//div[contains(@class, 'alert-success')]"
    MSG_ERRO_GERAL = "//div[contains(@class, 'alert-danger')]"
    MSG_ERRO_CAMPO = "//div[contains(@class, 'has-error')]//div[contains(@class, 'help-block')]"
    PRELOADER_CLASS = "preloader" 

    # Mapeamento Excel
    mapa = {
        'ID_cliente (*)': 'cliente_id', 'Cliente/Unidade': 'Nome do Cliente',
        'Segmento (*)': 'Segmento', 'Placa (*)': 'Placa', 'Chassi (*)': 'Chassis',
        'Renavam': 'Renavam', 'Ano de Fabricação (*)': 'Ano',
        'Autonomia': 'Autonomia', 'Marca (*)': 'Marca', 'Modelo (*)': 'Modelo',
        'Ano Modelo (*)': 'Ano Modelo', 'Cor  (*)': 'Cor',
        'Tanque de Combustivel (*)': 'Tanque de Comb',
        'Mes Licenciamento (*)': 'Mes de Licenciamento'
    }
    
    try:
        df_renomeado = df.rename(columns=mapa)
        lista_veiculos = df_renomeado.to_dict('records')
    except Exception as e:
        st.error(f"Erro no cabeçalho do arquivo: {e}")
        return False

    # Setup Navegador
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    
    service = Service()
    driver = None
    
    try:
        driver = webdriver.Chrome(service=service, options=chrome_options)
        wait = WebDriverWait(driver, 15)
        
        # --- 1. LOGIN ---
        status_text.info("Acessando sistema...")
        driver.get(URL_DO_SISTEMA)
        wait.until(EC.visibility_of_element_located((By.ID, ID_USUARIO))).send_keys(usuario)
        driver.find_element(By.ID, ID_SENHA).send_keys(senha)
        driver.find_element(By.XPATH, BTN_LOGIN).click()
        time.sleep(3)

        # --- 2. LOOP DE CADASTRO ---
        total = len(lista_veiculos)
        for i, item in enumerate(lista_veiculos):
            progress_bar.progress((i + 1) / total)
            
            placa = str(item.get('Placa', 'N/A')).strip()
            cliente_id = str(item.get('cliente_id', '')).replace('.0', '').strip()
            
            status_text.info(f"Processando {i+1}/{total}: {placa}...")

            if not cliente_id or cliente_id.lower() == 'nan':
                continue

            try:
                # ACESSO DIRETO
                driver.get(f"{URL_BASE_CADASTRO_VEICULO}{cliente_id}")
                
                # Espera carregamento
                try:
                    WebDriverWait(driver, 3).until(EC.invisibility_of_element_located((By.CLASS_NAME, PRELOADER_CLASS)))
                except: pass

                # --- PREENCHIMENTO ---
                
                # Placa Mercosul
                try:
                    radio = wait.until(EC.presence_of_element_located((By.XPATH, RADIO_MERCOSUL)))
                    driver.execute_script("arguments[0].click();", radio)
                except: pass

                # Segmento (Select2)
                try:
                    seg = str(item.get('Segmento', 'Outros')).capitalize()
                    driver.find_element(By.XPATH, SELECT2_SEGMENTO).click()
                    time.sleep(0.2)
                    opcao_xpath = f"//span[@class='select2-results']//li[text()='{seg}']"
                    wait.until(EC.element_to_be_clickable((By.XPATH, opcao_xpath))).click()
                except: pass

                # CAMPOS DE TEXTO (USANDO FORÇA BRUTA JS)
                input_force_js(driver, "input_veic_placa", placa)
                input_force_js(driver, "veiculo-veic_chassi", item.get('Chassis'))
                input_force_js(driver, "veiculo-veic_renavam", item.get('Renavam'))
                input_force_js(driver, "veiculo-veic_ano", item.get('Ano'))
                input_force_js(driver, "veiculo-veic_autonomia_fabrica", item.get('Autonomia', '0'))
                input_force_js(driver, "veiculo-veic_fabricante", item.get('Marca'))
                input_force_js(driver, "veiculo-veic_modelo", item.get('Modelo'))
                input_force_js(driver, "veiculo-veic_ano_modelo", item.get('Ano Modelo'))
                input_force_js(driver, "veiculo-veic_cor", item.get('Cor'))
                input_force_js(driver, "veiculo-veic_tanque_total", item.get('Tanque de Comb'))
                input_force_js(driver, "veiculo-mes_licenciamento", item.get('Mes de Licenciamento'))

                # NOVO: Tenta selecionar contrato se necessário
                tentar_selecionar_contrato(driver)

                # --- ENVIO (SUBMIT) ---
                time.sleep(1) # Respira para JS validar
                
                # Tenta submeter o formulário diretamente via JS (ignora cliques bloqueados)
                try:
                    driver.execute_script("document.getElementById('veiculo').submit();")
                except:
                    # Se falhar, tenta clicar no botão
                    btn = driver.find_element(By.XPATH, BTN_CADASTRAR)
                    driver.execute_script("arguments[0].click();", btn)

                # --- VALIDAÇÃO ---
                msg_encontrada = False
                tentativas = 0
                
                # Loop de verificação (5 segundos)
                while not msg_encontrada and tentativas < 5:
                    time.sleep(1)
                    tentativas += 1
                    
                    if driver.find_elements(By.XPATH, MSG_SUCESSO):
                        st.write(f"✅ **{placa}**: Sucesso!")
                        msg_encontrada = True
                        break
                    
                    erros = driver.find_elements(By.XPATH, MSG_ERRO_CAMPO)
                    if erros:
                        msg = erros[0].text
                        st.error(f"❌ **{placa}**: Validação falhou - {msg}")
                        driver.save_screenshot(f"erro_{placa}.png")
                        st.image(f"erro_{placa}.png")
                        msg_encontrada = True
                        break
                        
                    geral = driver.find_elements(By.XPATH, MSG_ERRO_GERAL)
                    if geral:
                        st.error(f"❌ **{placa}**: {geral[0].text}")
                        msg_encontrada = True
                        break

                if not msg_encontrada:
                    # Se chegou aqui, vamos ver os LOGS DO CONSOLE do navegador remoto
                    logs = driver.get_log('browser')
                    erros_console = [l['message'] for l in logs if l['level'] == 'SEVERE']
                    
                    st.warning(f"⚠️ **{placa}**: Timeout. Verifique a imagem.")
                    if erros_console:
                        st.error(f"Erros de JS detectados no site: {erros_console}")
                    
                    driver.save_screenshot(f"timeout_{placa}.png")
                    st.image(f"timeout_{placa}.png")

            except Exception as e:
                st.error(f"Erro crítico em {placa}: {e}")
                continue
                
        status_text.success("Processo Finalizado!")
        return True

    except Exception as e:
        status_text.error("Erro fatal.")
        st.error(e)
        return False
    finally:
        if driver:
            driver.quit()

# ==============================================================================
# INTERFACE
# ==============================================================================
st.set_page_config(page_title="Automação Veículos", layout="wide")
st.title("🤖 Cadastro de Veículos (Blindado)")

try:
    path = os.path.join(os.path.dirname(__file__), '..', 'modelo_importacao - Sheet1.csv')
    if not os.path.exists(path): path = 'modelo_importacao - Sheet1.csv'
    if os.path.exists(path):
        df_m = pd.read_csv(path)
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer) as writer: df_m.to_excel(writer, index=False)
        st.download_button("📄 Baixar Modelo XLSX", buffer.getvalue(), "modelo.xlsx")
except: pass

st.divider()

file = st.file_uploader("Arquivo de Dados", type=["xlsx", "csv"])
if file:
    try:
        df = pd.read_csv(file, skiprows=1) if file.name.endswith('.csv') else pd.read_excel(file, skiprows=1)
        if 'ID_cliente (*)' in df.columns:
            df = df[df['ID_cliente (*)'].notna()]
        
        st.info(f"{len(df)} veículos para cadastro.")
        
        c1, c2 = st.columns(2)
        user = c1.text_input("Usuário")
        pwd = c2.text_input("Senha", type="password")
        
        if st.button("🚀 Iniciar Cadastro", type="primary"):
            if user and pwd:
                executar_cadastro_veiculos(df, user, pwd, st.progress(0), st.empty())
            else:
                st.error("Preencha as credenciais.")
    except Exception as e:
        st.error(f"Erro ao ler arquivo: {e}")
