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
# FUNÇÕES AUXILIARES DE DIGITAÇÃO
# ==============================================================================
def preencher_campo_robusto(driver, element_id, value):
    """
    Tenta preencher o campo de forma robusta.
    1. Tenta digitar normalmente (send_keys).
    2. Se falhar ou ficar vazio, força via JavaScript.
    """
    if value and str(value).lower() != 'nan':
        value = str(value).replace('.0', '').strip()
        
        try:
            element = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, element_id)))
            
            # Rola até o elemento
            driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", element)
            time.sleep(0.3)
            
            # --- TENTATIVA 1: Digitação Padrão (Mais segura para máscaras) ---
            try:
                element.click()
                # Limpa com Backspace (melhor que .clear() para máscaras)
                element.send_keys(Keys.CONTROL + "a")
                element.send_keys(Keys.BACKSPACE)
                time.sleep(0.1)
                
                # Digita tudo de uma vez
                element.send_keys(value)
                time.sleep(0.2)
                element.send_keys(Keys.TAB)
            except Exception as e:
                print(f"Erro digitação padrão {element_id}: {e}")

            # --- VERIFICAÇÃO E CORREÇÃO ---
            # Se o campo estiver vazio após digitar (bug relatado), força JS
            valor_atual = element.get_attribute("value")
            
            if not valor_atual: 
                # --- TENTATIVA 2: Força Bruta JS (Fallback) ---
                # Apenas define o valor, sem disparar muitos eventos para não quebrar a máscara
                driver.execute_script("arguments[0].value = arguments[1];", element, value)
                # Dispara apenas o evento 'input' para o angular/vue/jquery perceber a mudança
                driver.execute_script("arguments[0].dispatchEvent(new Event('input', { bubbles: true }));", element)
            
        except Exception as e:
            print(f"Erro ao manipular campo {element_id}: {e}")

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

                # 3. Campos Texto (USANDO NOVA FUNÇÃO ROBUSTA)
                preencher_campo_robusto(driver, "input_veic_placa", placa)
                preencher_campo_robusto(driver, "veiculo-veic_chassi", item.get('Chassis'))
                preencher_campo_robusto(driver, "veiculo-veic_renavam", item.get('Renavam'))
                preencher_campo_robusto(driver, "veiculo-veic_ano", item.get('Ano'))
                preencher_campo_robusto(driver, "veiculo-veic_autonomia_fabrica", item.get('Autonomia', '0'))
                preencher_campo_robusto(driver, "veiculo-veic_fabricante", item.get('Marca'))
                preencher_campo_robusto(driver, "veiculo-veic_modelo", item.get('Modelo'))
                preencher_campo_robusto(driver, "veiculo-veic_ano_modelo", item.get('Ano Modelo'))
                preencher_campo_robusto(driver, "veiculo-veic_cor", item.get('Cor'))
                preencher_campo_robusto(driver, "veiculo-veic_tanque_total", item.get('Tanque de Comb'))
                preencher_campo_robusto(driver, "veiculo-mes_licenciamento", item.get('Mes de Licenciamento'))

                # 4. Contrato: REMOVIDO (Não toca no campo, deixa em branco)
                # tentar_selecionar_contrato(driver) 

                # --- ENVIO ---
                time.sleep(1) 
                
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
st.title("🤖 Cadastro de Veículos (Ajustado)")

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
