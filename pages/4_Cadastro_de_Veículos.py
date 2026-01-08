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
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# ==============================================================================
# FUNÇÃO PRINCIPAL DA AUTOMAÇÃO (VERSÃO ATUALIZADA - LAYOUT NOVO)
# ==============================================================================
def executar_cadastro_veiculos(df, usuario, senha, progress_bar, status_text):
    """
    Executa a automação de cadastro de veículos com correções para o novo formulário.
    """
    # --- CONFIGURAÇÕES E SELETORES (BASEADOS NO HTML FORNECIDO) ---
    URL_DO_SISTEMA = "https://sistema.etrac.com.br/"
    URL_BASE_CADASTRO_VEICULO = "https://sistema.etrac.com.br/index.php?r=veiculo%2Fcreate&id="
    
    # Seletores de Login
    ID_CAMPO_USUARIO = "loginform-username"
    ID_CAMPO_SENHA = "loginform-password"
    BOTAO_ENTRAR_XPATH = "//button[@name='login-button']"
    
    # Seletores do Formulário
    RADIO_PLACA_MERCOSUL_XPATH = "//input[@name='tipo_placa' and @value='2']"
    SELECT2_TIPO_VEICULO_BOX_XPATH = "//span[@aria-labelledby='select2-veiculo-veti_codigo-container']"
    
    # IDs dos Inputs (Confirmados no HTML)
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
    
    # Botão Cadastrar - XPath Genérico para encontrar dentro do grupo alinhado à direita
    BOTAO_CADASTRAR_VEICULO_XPATH = "//div[contains(@class, 'form-group align-right')]//button[contains(text(), 'Cadastrar')]"
    
    # Mensagens de Retorno
    MENSAGEM_SUCESSO_XPATH = "//div[contains(@class, 'alert-success') and contains(text(), 'Veículo salvo com sucesso')]"
    MENSAGEM_ERRO_GERAL_XPATH = "//div[contains(@class, 'alert-danger')]"
    MENSAGEM_ERRO_CAMPO_XPATH = "//div[contains(@class, 'has-error')]//div[contains(@class, 'help-block')]"

    # Mapeamento Excel -> Sistema
    mapa_colunas = {
        'ID_cliente (*)': 'cliente_id', 'Cliente/Unidade': 'Nome do Cliente',
        'Segmento (*)': 'Segmento', 'Placa (*)': 'Placa', 'Chassi (*)': 'Chassis',
        'Renavam': 'Renavam', 'Ano de Fabricação (*)': 'Ano',
        'Autonomia': 'Autonomia', 'Marca (*)': 'Marca', 'Modelo (*)': 'Modelo',
        'Ano Modelo (*)': 'Ano Modelo', 'Cor  (*)': 'Cor',
        'Tanque de Combustivel (*)': 'Tanque de Comb',
        'Mes Licenciamento (*)': 'Mes de Licenciamento'
    }
    
    # Renomeia colunas para facilitar acesso
    try:
        df_renomeado = df.rename(columns=mapa_colunas)
        lista_de_clientes = df_renomeado.to_dict('records')
    except Exception as e:
        st.error(f"Erro ao processar colunas do arquivo. Verifique o modelo. Detalhes: {e}")
        return False

    status_text.info("Configurando o navegador para ambiente de nuvem...")
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")

    service = Service()
    
    try:
        driver = webdriver.Chrome(service=service, options=chrome_options)
    except Exception as e:
        st.error(f"Erro ao iniciar o driver do Chrome. Verifique a instalação. {e}")
        return False
    
    wait = WebDriverWait(driver, 20) # Aumentado timeout para segurança
    total_veiculos = len(lista_de_clientes)

    try:
        status_text.info("1/3 - Acessando o sistema e realizando login...")
        driver.get(URL_DO_SISTEMA)
        
        wait.until(EC.presence_of_element_located((By.ID, ID_CAMPO_USUARIO))).send_keys(usuario)
        wait.until(EC.presence_of_element_located((By.ID, ID_CAMPO_SENHA))).send_keys(senha)
        wait.until(EC.element_to_be_clickable((By.XPATH, BOTAO_ENTRAR_XPATH))).click()
        
        status_text.info("Login realizado com sucesso. Aguardando carregamento...")
        time.sleep(3)

        status_text.info("2/3 - Iniciando o cadastro dos veículos...")
        for i, cliente in enumerate(lista_de_clientes):
            progresso = (i + 1) / total_veiculos
            progress_bar.progress(progresso)
            
            nome_cliente = cliente.get('Nome do Cliente', 'N/A')
            cliente_id = cliente.get('cliente_id')
            placa_veiculo = cliente.get('Placa', 'N/A')
            
            # Tratamento seguro para ID do cliente (remove decimais se houver)
            try:
                if pd.notna(cliente_id):
                    cliente_id = str(int(float(cliente_id)))
            except:
                cliente_id = str(cliente_id)

            status_text.info(f"Cadastrando veículo {i+1}/{total_veiculos} (Placa: {placa_veiculo})...")

            if not cliente_id or cliente_id == 'nan':
                st.warning(f"Registro para '{nome_cliente}' não possui 'ID_cliente' válido. Pulando...")
                continue
            
            try:
                # Navega direto para a tela de criação do cliente
                url_final = f"{URL_BASE_CADASTRO_VEICULO}{cliente_id}"
                driver.get(url_final)

                # 1. Seleciona Placa Mercosul (Radio Button)
                radio_mercosul = wait.until(EC.presence_of_element_located((By.XPATH, RADIO_PLACA_MERCOSUL_XPATH)))
                driver.execute_script("arguments[0].click();", radio_mercosul)
                time.sleep(0.5)

                # 2. Seleciona Segmento (Select2)
                segmento_veiculo = str(cliente.get('Segmento', 'Outros')).capitalize()
                
                # Clica no container do Select2 para abrir as opções
                select_tipo = wait.until(EC.element_to_be_clickable((By.XPATH, SELECT2_TIPO_VEICULO_BOX_XPATH)))
                select_tipo.click()
                
                # Clica na opção desejada na lista suspensa
                xpath_opcao_veiculo = f"//span[@class='select2-results']//li[text()='{segmento_veiculo}']"
                wait.until(EC.element_to_be_clickable((By.XPATH, xpath_opcao_veiculo))).click()
                
                # 3. Preenchimento dos campos de texto
                # Função auxiliar para preencher seguro e rolar se necessário
                def preencher_campo(by_id, valor):
                    if valor and str(valor).lower() != 'nan':
                        elem = driver.find_element(By.ID, by_id)
                        # Rola até o elemento para garantir que não está coberto
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", elem)
                        elem.clear()
                        elem.send_keys(str(valor))

                preencher_campo(INPUT_PLACA_ID, cliente.get('Placa', ''))
                preencher_campo(INPUT_CHASSI_ID, cliente.get('Chassis', ''))
                preencher_campo(INPUT_RENAVAM_ID, cliente.get('Renavam', ''))
                
                # Tratamento para campos numéricos que podem vir como float do Excel (ex: 2023.0 -> 2023)
                def formatar_inteiro(valor):
                    try:
                        return str(int(float(valor)))
                    except:
                        return str(valor)

                preencher_campo(INPUT_ANO_ID, formatar_inteiro(cliente.get('Ano', '')))
                preencher_campo(INPUT_AUTONOMIA_ID, cliente.get('Autonomia', '0'))
                preencher_campo(INPUT_FABRICANTE_ID, cliente.get('Marca', ''))
                preencher_campo(INPUT_MODELO_ID, cliente.get('Modelo', ''))
                preencher_campo(INPUT_ANO_MODELO_ID, formatar_inteiro(cliente.get('Ano Modelo', '')))
                preencher_campo(INPUT_COR_ID, cliente.get('Cor', ''))
                preencher_campo(INPUT_TANQUE_ID, formatar_inteiro(cliente.get('Tanque de Comb', '')))
                
                # Mês de Licenciamento
                mes_lic = cliente.get('Mes de Licenciamento', '')
                if pd.notna(mes_lic):
                    preencher_campo(INPUT_MES_LICENCIAMENTO_ID, formatar_inteiro(mes_lic))

                # --- CLIQUE NO BOTÃO CADASTRAR ---
                # Importante: Rolar até o fim da página para garantir que o botão não está oculto pelo footer
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1) 
                
                botao_cadastrar = wait.until(EC.presence_of_element_located((By.XPATH, BOTAO_CADASTRAR_VEICULO_XPATH)))
                # Garante que o botão está visível no centro da tela
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", botao_cadastrar)
                time.sleep(0.5)
                
                # Clica via JS para evitar interceptação
                driver.execute_script("arguments[0].click();", botao_cadastrar)
                
                # --- VERIFICAÇÃO DE SUCESSO ---
                try:
                    wait.until(EC.presence_of_element_located((By.XPATH, MENSAGEM_SUCESSO_XPATH)))
                    st.write(f"✅ **Confirmado:** Veículo '{placa_veiculo}' cadastrado para '{nome_cliente}'.")
                except TimeoutException:
                    try:
                        erro_campo_msg = driver.find_element(By.XPATH, MENSAGEM_ERRO_CAMPO_XPATH).text
                        st.error(f"❌ **Falha de Validação** para '{placa_veiculo}': {erro_campo_msg}")
                    except NoSuchElementException:
                        try:
                            erro_geral_msg = driver.find_element(By.XPATH, MENSAGEM_ERRO_GERAL_XPATH).text
                            st.error(f"❌ **Falha no Sistema** para '{placa_veiculo}': {erro_geral_msg}")
                        except NoSuchElementException:
                             st.warning(f"⚠️ **Sem Confirmação** para '{placa_veiculo}'. Verifique se foi salvo.")
                    continue

            except Exception as e:
                st.error(f"❌ Erro Crítico no processo da placa '{placa_veiculo}'. Pulando. Detalhe: {e}")
                continue
        
        status_text.success("3/3 - Processo de automação finalizado!")
        return True

    except Exception as e:
        status_text.error(f"‼️ OCORREU UM ERRO GERAL NO SCRIPT ‼️")
        st.error(f"Mensagem de erro: {e}")
        try:
            driver.save_screenshot("erro_geral_automacao.png")
            st.image("erro_geral_automacao.png")
        except:
            pass
        return False
    
    finally:
        if 'driver' in locals():
            driver.quit()

# ==============================================================================
# INTERFACE DO USUÁRIO COM STREAMLIT
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
    # Ajuste para garantir que o caminho do arquivo seja encontrado
    script_dir = os.path.dirname(__file__) 
    # Tenta localizar o arquivo modelo subindo um nível
    model_file_path = os.path.join(script_dir, '..', 'modelo_importacao - Sheet1.csv')
    
    # Se não encontrar, tenta no diretório atual (caso a estrutura seja diferente)
    if not os.path.exists(model_file_path):
        model_file_path = 'modelo_importacao - Sheet1.csv'

    # Lê o ficheiro CSV original para um DataFrame do pandas
    if os.path.exists(model_file_path):
        df_modelo = pd.read_csv(model_file_path)

        # Cria um buffer de bytes em memória para o ficheiro Excel
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_modelo.to_excel(writer, index=False, sheet_name='Sheet1')
        
        excel_data = output.getvalue()

        st.download_button(
            label="📄 Baixar Modelo de Importação (XLSX)",
            data=excel_data,
            file_name="modelo_importacao.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    else:
        st.warning("⚠️ Arquivo de modelo não encontrado no servidor.")
        
except Exception as e:
    st.error(f"Ocorreu um erro ao gerar o modelo XLSX: {e}")

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
        
        # Remove linhas vazias baseadas na coluna obrigatória
        if 'ID_cliente (*)' in df.columns:
            df.dropna(subset=['ID_cliente (*)'], inplace=True)
            # Remove possíveis .0 de IDs que vieram como float
            df['ID_cliente (*)'] = df['ID_cliente (*)'].astype(str).str.replace(r'\.0$', '', regex=True)
        
        st.success("Arquivo carregado e processado com sucesso!")
        st.dataframe(df.head())

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
