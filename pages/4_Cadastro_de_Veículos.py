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
# FUNÇÃO PRINCIPAL OTIMIZADA
# ==============================================================================
def executar_cadastro_veiculos(df, usuario, senha, progress_bar, status_text):
    # --- CONFIGURAÇÕES ---
    URL_DO_SISTEMA = "https://sistema.etrac.com.br/"
    URL_BASE_CADASTRO_VEICULO = "https://sistema.etrac.com.br/index.php?r=veiculo%2Fcreate&id="
    
    # IDs e XPaths
    ID_USUARIO = "loginform-username"
    ID_SENHA = "loginform-password"
    BTN_LOGIN = "//button[@name='login-button']"
    
    # Elementos da Tela de Cadastro
    RADIO_MERCOSUL = "//input[@name='tipo_placa' and @value='2']"
    SELECT2_SEGMENTO = "//span[@aria-labelledby='select2-veiculo-veti_codigo-container']"
    BTN_CADASTRAR = "//button[contains(text(), 'Cadastrar')]"
    
    # Mensagens de Retorno
    MSG_SUCESSO = "//div[contains(@class, 'alert-success')]"
    MSG_ERRO_GERAL = "//div[contains(@class, 'alert-danger')]"
    MSG_ERRO_CAMPO = "//div[contains(@class, 'has-error')]//div[contains(@class, 'help-block')]"
    MSG_ERRO_CONTRATO = "div_error_contrato" # ID específico do erro de contrato
    PRELOADER_CLASS = "preloader" # Classe da animação de carregamento

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
        
        # Espera login completar
        time.sleep(3)

        # --- 2. LOOP DE CADASTRO ---
        total = len(lista_veiculos)
        for i, item in enumerate(lista_veiculos):
            progress_bar.progress((i + 1) / total)
            
            placa = str(item.get('Placa', 'N/A')).strip()
            cliente_id = str(item.get('cliente_id', '')).replace('.0', '').strip()
            
            status_text.info(f"Processando {i+1}/{total}: {placa}...")

            if not cliente_id or cliente_id.lower() == 'nan':
                st.warning(f"Veículo {placa} sem ID de cliente. Pulando.")
                continue

            try:
                # Vai direto para URL de cadastro
                driver.get(f"{URL_BASE_CADASTRO_VEICULO}{cliente_id}")
                
                # Espera Preloader sumir (garante que a tela carregou)
                try:
                    WebDriverWait(driver, 3).until(EC.invisibility_of_element_located((By.CLASS_NAME, PRELOADER_CLASS)))
                except: pass

                # --- PREENCHIMENTO ---
                
                # 1. Tipo Placa (Mercosul)
                try:
                    radio = wait.until(EC.presence_of_element_located((By.XPATH, RADIO_MERCOSUL)))
                    driver.execute_script("arguments[0].click();", radio)
                    time.sleep(0.5) # Tempo pro JS da máscara atualizar
                except: pass

                # 2. Segmento (Select2)
                try:
                    seg = str(item.get('Segmento', 'Outros')).capitalize()
                    driver.find_element(By.XPATH, SELECT2_SEGMENTO).click()
                    opcao_xpath = f"//span[@class='select2-results']//li[text()='{seg}']"
                    wait.until(EC.element_to_be_clickable((By.XPATH, opcao_xpath))).click()
                except:
                    st.warning(f"Segmento '{seg}' não encontrado para {placa}. Usando padrão.")

                # 3. Campos de Texto (Limpeza Robusta com Backspace/Delete)
                def preencher(elem_id, valor):
                    if valor and str(valor).lower() != 'nan':
                        valor = str(valor).replace('.0', '')
                        try:
                            el = driver.find_element(By.ID, elem_id)
                            # Rola até o elemento
                            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", el)
                            # Limpa usando teclas (mais seguro contra máscaras)
                            el.send_keys(Keys.CONTROL + "a")
                            el.send_keys(Keys.DELETE)
                            el.send_keys(valor)
                        except Exception as e:
                            print(f"Erro campo {elem_id}: {e}")

                preencher("input_veic_placa", placa)
                preencher("veiculo-veic_chassi", item.get('Chassis'))
                preencher("veiculo-veic_renavam", item.get('Renavam'))
                preencher("veiculo-veic_ano", item.get('Ano'))
                preencher("veiculo-veic_autonomia_fabrica", item.get('Autonomia', '0'))
                preencher("veiculo-veic_fabricante", item.get('Marca'))
                preencher("veiculo-veic_modelo", item.get('Modelo'))
                preencher("veiculo-veic_ano_modelo", item.get('Ano Modelo'))
                preencher("veiculo-veic_cor", item.get('Cor'))
                preencher("veiculo-veic_tanque_total", item.get('Tanque de Comb'))
                preencher("veiculo-mes_licenciamento", item.get('Mes de Licenciamento'))

                # --- ENVIO ---
                # Rola para garantir visibilidade do botão e clica via JS
                btn = wait.until(EC.presence_of_element_located((By.XPATH, BTN_CADASTRAR)))
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                time.sleep(0.5)
                driver.execute_script("arguments[0].click();", btn)

                # --- VALIDAÇÃO DO RESULTADO ---
                # Espera ativa: aguarda surgir SUCESSO ou ERRO
                msg_encontrada = False
                tentativas = 0
                
                while not msg_encontrada and tentativas < 5:
                    time.sleep(1)
                    tentativas += 1
                    
                    # 1. Verifica Sucesso
                    if driver.find_elements(By.XPATH, MSG_SUCESSO):
                        st.write(f"✅ **{placa}**: Cadastrado com sucesso!")
                        msg_encontrada = True
                        break
                    
                    # 2. Verifica Erros de Validação (Campos vermelhos)
                    erros = driver.find_elements(By.XPATH, MSG_ERRO_CAMPO)
                    if erros:
                        msg = erros[0].text
                        st.error(f"❌ **{placa}**: Erro no campo - {msg}")
                        driver.save_screenshot(f"erro_{placa}.png")
                        st.image(f"erro_{placa}.png")
                        msg_encontrada = True
                        break
                        
                    # 3. Verifica Erro Geral
                    geral = driver.find_elements(By.XPATH, MSG_ERRO_GERAL)
                    if geral:
                        st.error(f"❌ **{placa}**: {geral[0].text}")
                        msg_encontrada = True
                        break

                    # 4. Verifica Erro Específico de Contrato
                    try:
                        err_contrato = driver.find_element(By.ID, MSG_ERRO_CONTRATO)
                        if err_contrato.is_displayed():
                            st.error(f"❌ **{placa}**: Bloqueio de Contrato (Sem limite disponível).")
                            msg_encontrada = True
                            break
                    except: pass

                if not msg_encontrada:
                    st.warning(f"⚠️ **{placa}**: Sem confirmação visual (Timeout). Verifique o print.")
                    driver.save_screenshot(f"timeout_{placa}.png")
                    st.image(f"timeout_{placa}.png")

            except Exception as e:
                st.error(f"Erro crítico ao processar {placa}: {e}")
                continue
                
        status_text.success("Processo Finalizado!")
        return True

    except Exception as e:
        status_text.error("Erro fatal no driver.")
        st.error(e)
        return False
    finally:
        if driver:
            driver.quit()

# ==============================================================================
# INTERFACE
# ==============================================================================
st.set_page_config(page_title="Automação Veículos", layout="wide")
st.title("🤖 Cadastro Automático de Veículos")

# Download Modelo (Simplificado)
try:
    path = os.path.join(os.path.dirname(__file__), '..', 'modelo_importacao - Sheet1.csv')
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
        # Filtra linhas vazias
        if 'ID_cliente (*)' in df.columns:
            df = df[df['ID_cliente (*)'].notna()]
        
        st.info(f"{len(df)} veículos identificados.")
        
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
