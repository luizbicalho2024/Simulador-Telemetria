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
# FUNÇÕES AUXILIARES DE DIGITAÇÃO HUMANA
# ==============================================================================
def digitar_humanizado(driver, element_id, value):
    """
    Simula a digitação humana para não quebrar o InputMask (jQuery).
    Limpa o campo com Backspace e digita letra por letra.
    """
    if value and str(value).lower() != 'nan':
        value = str(value).replace('.0', '').strip()
        try:
            element = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, element_id)))
            
            # Rola suavemente até o elemento
            driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", element)
            time.sleep(0.2)
            
            # 1. Foca no campo
            element.click()
            time.sleep(0.1)
            
            # 2. Limpeza Cirúrgica (Backspace é mais seguro para máscaras)
            current_val = element.get_attribute("value")
            if current_val:
                element.send_keys(Keys.END) # Vai pro final
                # Apaga tudo + 3 vezes por segurança
                for _ in range(len(current_val) + 3):
                    element.send_keys(Keys.BACKSPACE)
            
            # 3. Digitação Lenta
            for char in value:
                element.send_keys(char)
                time.sleep(0.02) # Delay imperceptível mas funcional
            
            # 4. Sai do campo para disparar validação (Blur)
            element.send_keys(Keys.TAB)
            time.sleep(0.2)
            
        except Exception as e:
            print(f"Erro ao digitar em {element_id}: {e}")

def tentar_selecionar_contrato(driver):
    """
    Tenta selecionar o contrato se o campo estiver visível e vazio.
    """
    try:
        # XPath do container do Select2 do contrato
        SELECT2_CONTRATO = "//span[@aria-labelledby='select2-veiculo-contrato_vinculo_veiculo-container']"
        
        # Verifica se existe e clica
        elementos = driver.find_elements(By.XPATH, SELECT2_CONTRATO)
        if elementos:
            # Verifica se já tem valor selecionado (opcional, mas bom pra evitar reset)
            titulo = elementos[0].get_attribute("title")
            if not titulo or "Selecione" in titulo:
                elementos[0].click()
                time.sleep(0.5)
                
                # Seleciona a primeira opção real disponível
                OPCAO_VALIDA = "//li[contains(@class, 'select2-results__option') and not(contains(@class, 'loading'))]"
                opcoes = WebDriverWait(driver, 3).until(EC.presence_of_all_elements_located((By.XPATH, OPCAO_VALIDA)))
                
                # Clica na primeira ou segunda opção (dependendo se a primeira é o placeholder)
                if len(opcoes) > 0:
                    # Tenta clicar na última opção (geralmente os contratos mais recentes ficam no fim ou início)
                    # Ou simplesmente clica na segunda opção se a primeira for vazia
                    opcoes[-1].click() 
    except:
        pass

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
    
    MSG_SUCESSO = "//div[contains(@class, 'alert-success')]"
    MSG_ERRO_GERAL = "//div[contains(@class, 'alert-danger')]"
    MSG_ERRO_CAMPO = "//div[contains(@class, 'has-error')]//div[contains(@class, 'help-block')]"
    PRELOADER_CLASS = "preloader"

    # Mapeamento
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
        st.error(f"Erro colunas: {e}")
        return False

    # Setup Chrome
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
        wait = WebDriverWait(driver, 20)
        
        # --- LOGIN ---
        status_text.info("Fazendo login...")
        driver.get(URL_DO_SISTEMA)
        wait.until(EC.visibility_of_element_located((By.ID, ID_USUARIO))).send_keys(usuario)
        driver.find_element(By.ID, ID_SENHA).send_keys(senha)
        driver.find_element(By.XPATH, BTN_LOGIN).click()
        time.sleep(3)

        # --- LOOP ---
        total = len(lista_veiculos)
        for i, item in enumerate(lista_veiculos):
            progress_bar.progress((i + 1) / total)
            placa = str(item.get('Placa', 'N/A')).strip()
            cliente_id = str(item.get('cliente_id', '')).replace('.0', '').strip()
            
            status_text.info(f"Processando: {placa}...")

            if not cliente_id or cliente_id.lower() == 'nan':
                continue

            try:
                driver.get(f"{URL_BASE_CADASTRO_VEICULO}{cliente_id}")
                
                # Espera Preloader
                try:
                    WebDriverWait(driver, 5).until(EC.invisibility_of_element_located((By.CLASS_NAME, PRELOADER_CLASS)))
                except: pass

                # --- PREENCHIMENTO ---
                # 1. Tipo Placa
                try:
                    radio = wait.until(EC.presence_of_element_located((By.XPATH, RADIO_MERCOSUL)))
                    driver.execute_script("arguments[0].click();", radio)
                    time.sleep(0.5)
                except: pass

                # 2. Segmento
                try:
                    seg = str(item.get('Segmento', 'Outros')).capitalize()
                    driver.find_element(By.XPATH, SELECT2_SEGMENTO).click()
                    time.sleep(0.3)
                    xp = f"//span[@class='select2-results']//li[text()='{seg}']"
                    wait.until(EC.element_to_be_clickable((By.XPATH, xp))).click()
                except: pass

                # 3. Campos Texto (Método Humano)
                digitar_humanizado(driver, "input_veic_placa", placa)
                digitar_humanizado(driver, "veiculo-veic_chassi", item.get('Chassis'))
                digitar_humanizado(driver, "veiculo-veic_renavam", item.get('Renavam'))
                digitar_humanizado(driver, "veiculo-veic_ano", item.get('Ano'))
                digitar_humanizado(driver, "veiculo-veic_autonomia_fabrica", item.get('Autonomia', '0'))
                digitar_humanizado(driver, "veiculo-veic_fabricante", item.get('Marca'))
                digitar_humanizado(driver, "veiculo-veic_modelo", item.get('Modelo'))
                digitar_humanizado(driver, "veiculo-veic_ano_modelo", item.get('Ano Modelo'))
                digitar_humanizado(driver, "veiculo-veic_cor", item.get('Cor'))
                digitar_humanizado(driver, "veiculo-veic_tanque_total", item.get('Tanque de Comb'))
                digitar_humanizado(driver, "veiculo-mes_licenciamento", item.get('Mes de Licenciamento'))

                # 4. Contrato (NOVO)
                tentar_selecionar_contrato(driver)

                # --- ENVIO ---
                time.sleep(1) # Aguarda validações finais
                
                # Tenta submeter
                try:
                    # Clica via JS no botão salvar
                    btn = driver.find_element(By.XPATH, BTN_CADASTRAR)
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                    time.sleep(0.5)
                    driver.execute_script("arguments[0].click();", btn)
                except:
                    # Fallback: Submit form
                    driver.execute_script("document.getElementById('veiculo').submit();")

                # --- CHECK FINAL ---
                msg_encontrada = False
                tentativas = 0
                while not msg_encontrada and tentativas < 5:
                    time.sleep(1.5)
                    tentativas += 1
                    
                    if driver.find_elements(By.XPATH, MSG_SUCESSO):
                        st.write(f"✅ **{placa}**: Sucesso!")
                        msg_encontrada = True
                        break
                    
                    # Checa erro de campo
                    erros = driver.find_elements(By.XPATH, MSG_ERRO_CAMPO)
                    if erros:
                        visiveis = [e for e in erros if e.is_displayed()]
                        if visiveis:
                            st.error(f"❌ **{placa}**: Validação - {visiveis[0].text}")
                            driver.save_screenshot(f"erro_{placa}.png")
                            st.image(f"erro_{placa}.png")
                            msg_encontrada = True
                            break
                    
                    # Checa erro geral
                    geral = driver.find_elements(By.XPATH, MSG_ERRO_GERAL)
                    if geral and geral[0].is_displayed():
                        st.error(f"❌ **{placa}**: {geral[0].text}")
                        msg_encontrada = True
                        break

                if not msg_encontrada:
                    st.warning(f"⚠️ **{placa}**: Timeout. Verifique print.")
                    driver.save_screenshot(f"timeout_{placa}.png")
                    st.image(f"timeout_{placa}.png")

            except Exception as e:
                st.error(f"Erro em {placa}: {e}")
                continue
                
        status_text.success("Finalizado!")
        return True

    except Exception as e:
        status_text.error(f"Erro geral: {e}")
        return False
    finally:
        if driver:
            driver.quit()

# ==============================================================================
# UI STREAMLIT
# ==============================================================================
st.set_page_config(page_title="Automação Veículos", layout="wide")
st.title("🤖 Cadastro de Veículos (Modo Compatibilidade)")

try:
    path = os.path.join(os.path.dirname(__file__), '..', 'modelo_importacao - Sheet1.csv')
    if not os.path.exists(path): path = 'modelo_importacao - Sheet1.csv'
    if os.path.exists(path):
        df_m = pd.read_csv(path)
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer) as writer: df_m.to_excel(writer, index=False)
        st.download_button("📄 Modelo XLSX", buffer.getvalue(), "modelo.xlsx")
except: pass

st.divider()

file = st.file_uploader("Arquivo", type=["xlsx", "csv"])
if file:
    try:
        df = pd.read_csv(file, skiprows=1) if file.name.endswith('.csv') else pd.read_excel(file, skiprows=1)
        if 'ID_cliente (*)' in df.columns:
            df = df[df['ID_cliente (*)'].notna()]
        
        st.info(f"Veículos para cadastro: {len(df)}")
        
        c1, c2 = st.columns(2)
        user = c1.text_input("Usuário")
        pwd = c2.text_input("Senha", type="password")
        
        if st.button("🚀 Iniciar", type="primary"):
            if user and pwd:
                executar_cadastro_veiculos(df, user, pwd, st.progress(0), st.empty())
            else:
                st.error("Informe usuário e senha.")
    except Exception as e:
        st.error(f"Erro arquivo: {e}")
