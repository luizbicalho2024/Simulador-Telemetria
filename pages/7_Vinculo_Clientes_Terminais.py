# pages/🔗_Vinculo_Clientes_Terminais.py
import streamlit as st
import pandas as pd
import user_management_db as umdb
import json

# --- 1. CONFIGURAÇÃO E AUTENTICAÇÃO ---
st.set_page_config(
    layout="wide",
    page_title="Vínculo de Clientes e Terminais",
    page_icon="🔗"
)

if not st.session_state.get("authentication_status"):
    st.error("🔒 Acesso Negado! Por favor, faça login para visualizar esta página.")
    st.stop()

# --- 2. FUNÇÃO AUXILIAR ROBUSTA COM DEBUG ---
@st.cache_data
def processar_vinculos(file_clientes, file_rastreadores):
    """
    Lê as duas planilhas, processa a estrutura aninhada dos clientes de forma robusta e
    junta com as informações de modelo dos rastreadores.
    """
    try:
        # === ETAPA 1: PREPARAR MAPA DE RASTREADORES ===
        st.write("🔍 **Debug:** Processando arquivo de rastreadores...")
        df_rastreadores = pd.read_excel(file_rastreadores, header=11, engine='openpyxl')
        
        # Debug: Mostrar colunas disponíveis
        st.write(f"📊 Colunas encontradas no arquivo de rastreadores: {list(df_rastreadores.columns)}")
        
        # Procurar especificamente pela coluna "Nº Série" (chave de ligação)
        coluna_serie = None
        coluna_modelo = None
        
        for col in df_rastreadores.columns:
            col_lower = str(col).lower().strip()
            # Priorizar "Nº Série" como mencionado pelo usuário
            if 'nº série' in col_lower or 'n° série' in col_lower:
                coluna_serie = col
            elif any(term in col_lower for term in ['série', 'serie', 'serial', 'numero']):
                if coluna_serie is None:  # Só usar como fallback
                    coluna_serie = col
            elif any(term in col_lower for term in ['modelo', 'model']):
                coluna_modelo = col
        
        if not coluna_serie:
            st.error("❌ Coluna 'Nº Série' não encontrada no arquivo de rastreadores!")
            st.write("🔍 Colunas disponíveis:", list(df_rastreadores.columns))
            return None, None
            
        if not coluna_modelo:
            st.error("❌ Coluna 'Modelo' não encontrada no arquivo de rastreadores!")
            st.write("🔍 Colunas disponíveis:", list(df_rastreadores.columns))
            return None, None
            
        st.write(f"✅ **Colunas identificadas:** Série='{coluna_serie}', Modelo='{coluna_modelo}'")
        
        # Renomear para padronizar
        df_rastreadores = df_rastreadores.rename(columns={coluna_serie: 'Numero_Serie', coluna_modelo: 'Modelo_Rastreador'})
        df_rastreadores.dropna(subset=['Numero_Serie'], inplace=True)
        
        # Limpar e padronizar números de série (chave de ligação)
        df_rastreadores['Numero_Serie_Clean'] = df_rastreadores['Numero_Serie'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
        
        # Criar mapa: Número de Série → Modelo
        mapa_modelos = df_rastreadores.set_index('Numero_Serie_Clean')['Modelo_Rastreador'].to_dict()
        
        st.write(f"✅ **Debug:** {len(mapa_modelos)} rastreadores carregados")
        st.write(f"🔑 **Exemplo de números de série:** {list(mapa_modelos.keys())[:5]}")

        # === ETAPA 2: INVESTIGAR ESTRUTURA DO ARQUIVO DE CLIENTES ===
        st.write("🔍 **Debug:** Investigando estrutura do arquivo de clientes...")
        
        # Tentar diferentes linhas de cabeçalho
        possible_headers = [0, 1, 2, 3, 4, 5, 10, 11, 12, 13, 14, 15]
        df_clientes_raw = None
        header_encontrado = None
        
        for header_line in possible_headers:
            try:
                df_test = pd.read_excel(file_clientes, header=header_line, engine='openpyxl')
                st.write(f"🔍 **Testando linha {header_line} como cabeçalho:**")
                st.write(f"   Colunas: {list(df_test.columns)}")
                
                # Verificar se esta linha tem mais colunas úteis
                colunas_uteis = 0
                for col in df_test.columns:
                    col_str = str(col).lower().strip()
                    if any(term in col_str for term in ['terminal', 'frota', 'rastreador', 'equipamento', 'série', 'nome', 'cliente']):
                        colunas_uteis += 1
                
                st.write(f"   Colunas úteis encontradas: {colunas_uteis}")
                
                # Se encontrou mais colunas úteis ou dados mais completos
                if colunas_uteis >= 3 or any('terminal' in str(col).lower() for col in df_test.columns):
                    df_clientes_raw = df_test
                    header_encontrado = header_line
                    st.write(f"✅ **Usando linha {header_line} como cabeçalho**")
                    break
                    
            except Exception as e:
                st.write(f"   Erro na linha {header_line}: {str(e)}")
                continue
        
        # Se não encontrou cabeçalho adequado, usar linha 11 mesmo assim
        if df_clientes_raw is None:
            st.warning("⚠️ Não foi encontrado cabeçalho ideal. Usando linha 11 e investigando dados...")
            df_clientes_raw = pd.read_excel(file_clientes, header=11, engine='openpyxl')
            header_encontrado = 11
        
        # Debug: Mostrar mais informações
        st.write(f"📊 **Arquivo de clientes (cabeçalho linha {header_encontrado}):**")
        st.write(f"   Colunas: {list(df_clientes_raw.columns)}")
        st.write(f"   Shape: {df_clientes_raw.shape}")
        
        # Mostrar mais linhas para investigação
        st.write("📋 **Debug:** Primeiras 10 linhas do arquivo:")
        st.dataframe(df_clientes_raw.head(10))
        
        # Investigar se os dados de terminal estão nas próprias células
        st.write("🔍 **Investigando conteúdo das células para encontrar terminais/rastreadores...**")
        
        # Procurar por padrões numéricos que possam ser rastreadores
        for index, row in df_clientes_raw.head(20).iterrows():
            for col in df_clientes_raw.columns:
                valor = str(row[col])
                # Procurar por números que parecem ser rastreadores (6-12 dígitos)
                if valor.isdigit() and 6 <= len(valor) <= 12:
                    st.write(f"   🔢 Possível rastreador: '{valor}' na coluna '{col}' (linha {index})")
        
        # Remove colunas completamente vazias
        df_clientes_raw = df_clientes_raw.loc[:, ~df_clientes_raw.columns.str.contains('^Unnamed', na=False)]
        df_clientes_raw.dropna(how='all', inplace=True)
        
        # NOVA ABORDAGEM: Processar sem depender de colunas específicas
        # Vamos procurar padrões nos dados mesmo sem colunas explícitas
        
        st.write("🔄 **Nova abordagem:** Processando sem depender de nomes de colunas específicas...")
        
        # Identificar colunas por conteúdo, não só por nome
        colunas_mapeadas = {}
        
        for col in df_clientes_raw.columns:
            col_lower = str(col).lower().strip()
            
            # Mapear por nome da coluna
            if any(term in col_lower for term in ['nome', 'razão social']) and 'cliente' in col_lower:
                colunas_mapeadas['nome'] = col
            elif any(term in col_lower for term in ['cpf', 'cnpj']):
                colunas_mapeadas['documento'] = col
            elif 'tipo' in col_lower and 'cliente' in col_lower:
                colunas_mapeadas['tipo'] = col
            elif any(term in col_lower for term in ['terminal', 'frota']):
                colunas_mapeadas['terminal'] = col
            elif any(term in col_lower for term in ['rastreador', 'equipamento', 'série']):
                colunas_mapeadas['rastreador'] = col
        
        # Se não encontrou terminal/rastreador por nome, tentar identificar por conteúdo
        if 'terminal' not in colunas_mapeadas or 'rastreador' not in colunas_mapeadas:
            st.write("🔍 **Tentando identificar colunas por conteúdo dos dados...**")
            
            for col in df_clientes_raw.columns:
                if col in [colunas_mapeadas.get('nome'), colunas_mapeadas.get('documento'), colunas_mapeadas.get('tipo')]:
                    continue
                    
                # Analisar o conteúdo da coluna
                valores_numericos = 0
                valores_texto_curto = 0
                valores_validos = 0
                
                for valor in df_clientes_raw[col].dropna().head(50):
                    valor_str = str(valor).strip()
                    if valor_str and valor_str != 'nan':
                        valores_validos += 1
                        if valor_str.replace('.', '').replace(',', '').isdigit():
                            valores_numericos += 1
                        elif len(valor_str) <= 50:
                            valores_texto_curto += 1
                
                if valores_validos > 0:
                    perc_numericos = valores_numericos / valores_validos
                    perc_texto = valores_texto_curto / valores_validos
                    
                    st.write(f"   Coluna '{col}': {valores_validos} valores, {perc_numericos:.1%} numéricos, {perc_texto:.1%} texto")
                    
                    # Se tem muitos números, pode ser rastreador
                    if perc_numericos > 0.5 and 'rastreador' not in colunas_mapeadas:
                        colunas_mapeadas['rastreador'] = col
                        st.write(f"   ✅ Identificada como possível coluna de rastreador")
                    # Se tem texto curto, pode ser terminal
                    elif perc_texto > 0.5 and 'terminal' not in colunas_mapeadas:
                        colunas_mapeadas['terminal'] = col
                        st.write(f"   ✅ Identificada como possível coluna de terminal")
        
        st.write(f"🗂️ **Colunas mapeadas:** {colunas_mapeadas}")
        
        # Se ainda não tem as colunas essenciais, tentar abordagem alternativa
        if not all(key in colunas_mapeadas for key in ['nome', 'documento']):
            st.error("❌ Não foi possível identificar nem mesmo as colunas básicas de cliente!")
            st.info("💡 O arquivo pode estar em um formato muito diferente do esperado.")
            return None, None
        
        # Continuar mesmo sem terminal/rastreador para investigar a estrutura
        st.write("📋 **Continuando processamento para investigar estrutura dos dados...**")

        # === ETAPA 3: PROCESSAR REGISTROS DE FORMA ADAPTATIVA ===
        registos_consolidados = []
        cliente_atual = None
        linhas_processadas = 0
        clientes_encontrados = 0
        terminais_encontrados = 0

        for index, row in df_clientes_raw.iterrows():
            linhas_processadas += 1
            
            # Obter valores das colunas mapeadas (com fallback)
            nome_cliente = row.get(colunas_mapeadas.get('nome', ''), '') if 'nome' in colunas_mapeadas else ''
            documento = row.get(colunas_mapeadas.get('documento', ''), '') if 'documento' in colunas_mapeadas else ''
            tipo_cliente = str(row.get(colunas_mapeadas.get('tipo', ''), '')).strip() if 'tipo' in colunas_mapeadas else ''
            terminal = row.get(colunas_mapeadas.get('terminal', ''), '') if 'terminal' in colunas_mapeadas else ''
            rastreador = row.get(colunas_mapeadas.get('rastreador', ''), '') if 'rastreador' in colunas_mapeadas else ''
            
            # Se não temos colunas de terminal/rastreador, procurar em todas as colunas
            if not terminal or not rastreador:
                for col in df_clientes_raw.columns:
                    if col not in [colunas_mapeadas.get('nome'), colunas_mapeadas.get('documento'), colunas_mapeadas.get('tipo')]:
                        valor = str(row.get(col, '')).strip()
                        
                        # Se parece um rastreador (número de 6-12 dígitos)
                        if valor.replace('.', '').isdigit() and 6 <= len(valor.replace('.', '')) <= 12:
                            rastreador = valor
                        # Se parece um terminal (texto alfanumérico curto)
                        elif valor and len(valor) <= 20 and valor.replace(' ', '').replace('-', '').isalnum():
                            terminal = valor
            
            # === IDENTIFICAR LINHA DE CLIENTE ===
            nome_valido = pd.notna(nome_cliente) and str(nome_cliente).strip() != '' and str(nome_cliente).strip().lower() not in ['terminal', 'nome do cliente']
            documento_valido = pd.notna(documento) and str(documento).strip() != '' and str(documento).strip().lower() not in ['cpf/cnpj']
            
            # Verificar se é uma linha de dados válida (não cabeçalho)
            if nome_valido and documento_valido:
                # Verificar se não é uma linha de cabeçalho repetida
                nome_str = str(nome_cliente).strip()
                if nome_str.lower() not in ['nome do cliente', 'cliente', 'razão social']:
                    # Esta é uma linha de cliente
                    cliente_atual = {
                        'Nome do Cliente': nome_str,
                        'CPF/CNPJ': str(documento).strip(),
                        'Tipo Cliente': tipo_cliente if tipo_cliente else 'Não especificado'
                    }
                    clientes_encontrados += 1
                    st.write(f"👤 **Cliente encontrado #{clientes_encontrados}:** {cliente_atual['Nome do Cliente']}")
                    
                    # Verificar se a mesma linha já tem terminal/rastreador
                    if terminal and rastreador and str(terminal).strip() != '' and str(rastreador).strip() != '':
                        registos_consolidados.append({
                            **cliente_atual,
                            'Terminal/Frota': str(terminal).strip(),
                            'Rastreador': str(rastreador).replace('.0', '').strip()
                        })
                        terminais_encontrados += 1
                        st.write(f"  📱 Terminal na mesma linha: {str(terminal).strip()} → {str(rastreador).strip()}")
                    
                    continue
            
            # === PROCESSAR LINHA DE TERMINAL/DADOS ADICIONAIS ===
            if cliente_atual is not None:
                # Mesmo sem colunas específicas, procurar dados úteis na linha
                terminal_encontrado = None
                rastreador_encontrado = None
                
                for col in df_clientes_raw.columns:
                    valor = str(row.get(col, '')).strip()
                    if valor and valor != 'nan':
                        # Identificar rastreador por padrão numérico
                        if valor.replace('.', '').replace(',', '').isdigit() and 6 <= len(valor.replace('.', '').replace(',', '')) <= 12:
                            rastreador_encontrado = valor.replace('.0', '').replace(',', '')
                        # Identificar terminal por padrão alfanumérico curto
                        elif len(valor) <= 30 and any(c.isalnum() for c in valor):
                            # Ignorar valores que são claramente outros tipos de dados
                            if not any(palavra in valor.lower() for palavra in ['telefone', 'email', 'endereço', 'rua', 'cidade']):
                                terminal_encontrado = valor
                
                # Se encontrou dados válidos, adicionar
                if terminal_encontrado and rastreador_encontrado:
                    registos_consolidados.append({
                        **cliente_atual,
                        'Terminal/Frota': terminal_encontrado,
                        'Rastreador': rastreador_encontrado
                    })
                    terminais_encontrados += 1
                    st.write(f"  📱 Dados encontrados: {terminal_encontrado} → {rastreador_encontrado}")
                
                # Debug: mostrar linha processada
                elif any(str(row.get(col, '')).strip() for col in df_clientes_raw.columns):
                    valores_linha = [f"{col}: '{row.get(col, '')}'" for col in df_clientes_raw.columns if str(row.get(col, '')).strip()]
                    if valores_linha:
                        st.write(f"  🔍 Linha analisada: {valores_linha[:3]}...")  # Primeiros 3 valores

        # Debug final
        st.write(f"📈 **Debug:** Processadas {linhas_processadas} linhas")
        st.write(f"👥 **Debug:** {clientes_encontrados} clientes identificados")
        st.write(f"📱 **Debug:** {terminais_encontrados} terminais encontrados")
        st.write(f"🔗 **Debug:** {len(registos_consolidados)} vínculos consolidados")

        # === ETAPA 4: CRIAR DATAFRAME FINAL E FAZER LIGAÇÃO ===
        if not registos_consolidados:
            st.error("❌ Nenhum vínculo foi consolidado. Verifique a estrutura dos dados.")
            return None, None

        df_final = pd.DataFrame(registos_consolidados)
        
        # Limpar números de rastreador para fazer a ligação correta
        df_final['Rastreador_Clean'] = df_final['Rastreador'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
        
        # Fazer a ligação: Rastreador (clientes) → Nº Série (rastreadores) → Modelo
        df_final['Modelo'] = df_final['Rastreador_Clean'].map(mapa_modelos).fillna('Modelo não encontrado')
        
        # Debug: Verificar ligações
        st.write(f"🔗 **Debug ligação:** {len(df_final)} registros processados")
        
        # Mostrar alguns exemplos da ligação
        if len(df_final) > 0:
            st.write("🔍 **Exemplos de ligação Rastreador → Modelo:**")
            for i, row in df_final.head(3).iterrows():
                rastreador = row['Rastreador_Clean']
                modelo = row['Modelo']
                st.write(f"  • Rastreador: {rastreador} → Modelo: {modelo}")
        
        # Verificar rastreadores não encontrados
        rastreadores_nao_encontrados = df_final[df_final['Modelo'] == 'Modelo não encontrado']['Rastreador_Clean'].unique()
        if len(rastreadores_nao_encontrados) > 0:
            st.warning(f"⚠️ **{len(rastreadores_nao_encontrados)} rastreadores sem modelo encontrado:**")
            st.write(f"Rastreadores não encontrados: {list(rastreadores_nao_encontrados)[:10]}")
            
            # Sugerir rastreadores similares
            if len(rastreadores_nao_encontrados) > 0:
                exemplo_nao_encontrado = rastreadores_nao_encontrados[0]
                rastreadores_disponiveis = list(mapa_modelos.keys())[:10]
                st.write(f"💡 **Comparação de exemplo:**")
                st.write(f"   Não encontrado: '{exemplo_nao_encontrado}'")
                st.write(f"   Disponíveis: {rastreadores_disponiveis}")
        
        # Remover coluna auxiliar
        df_final_clean = df_final[['Nome do Cliente', 'CPF/CNPJ', 'Tipo Cliente', 'Terminal/Frota', 'Rastreador', 'Modelo']]

        # === ETAPA 5: AGRUPAR PARA JSON ===
        df_grouped = df_final_clean.groupby(['Nome do Cliente', 'CPF/CNPJ', 'Tipo Cliente']).apply(
            lambda x: x[['Terminal/Frota', 'Rastreador', 'Modelo']].to_dict('records')
        ).reset_index(name='Terminais')

        json_resultado = json.loads(df_grouped.to_json(orient="records", force_ascii=False))

        return df_final_clean, json_resultado

    except Exception as e:
        st.error(f"💥 Erro inesperado: {str(e)}")
        st.exception(e)  # Mostra stack trace completo
        return None, None

# --- 3. INTERFACE DA PÁGINA ---
st.sidebar.image("imgs/v-c.png", width=120)
st.sidebar.title(f"Olá, {st.session_state.get('name', 'N/A')}! 👋")
st.sidebar.markdown("---")

try:
    st.image("imgs/logo.png", width=250)
except: 
    pass

st.markdown("<h1 style='text-align: center; color: #006494;'>🔗 Vínculo de Clientes e Terminais</h1>", unsafe_allow_html=True)
st.markdown("---")

# --- 4. UPLOAD DOS FICHEIROS ---
st.subheader("Carregamento dos Relatórios da Etrac")
col1, col2 = st.columns(2)

with col1:
    st.info("**1. Relatório de Clientes**")
    uploaded_clientes = st.file_uploader("Carregue o `relatorio_clientes.xlsx`", type=['xlsx'], key="clientes_upload")

with col2:
    st.info("**2. Relatório de Rastreadores (Estoque)**")
    uploaded_rastreadores = st.file_uploader("Carregue o `relatorio_rastreador.xlsx`", type=['xlsx'], key="rastreadores_upload")

st.markdown("---")

# --- 5. ANÁLISE E EXIBIÇÃO ---
if uploaded_clientes and uploaded_rastreadores:
    try:
        # Adicionar checkbox para debug
        debug_mode = st.checkbox("🔧 Modo Debug (mostrar informações detalhadas)", value=True)
        
        with st.spinner("A processar e a comparar as planilhas..."):
            if debug_mode:
                df_tabela, dados_json = processar_vinculos(uploaded_clientes, uploaded_rastreadores)
            else:
                # Para modo produção, criar versão sem debug
                st.info("Modo produção ainda não implementado. Usando modo debug.")
                df_tabela, dados_json = processar_vinculos(uploaded_clientes, uploaded_rastreadores)
        
        if df_tabela is not None and not df_tabela.empty:
            st.success(f"✅ Análise concluída! Foram encontrados **{len(df_tabela)}** terminais vinculados a **{df_tabela['CPF/CNPJ'].nunique()}** clientes distintos.")
            
            # Métricas
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total de Vínculos", len(df_tabela))
            with col2:
                st.metric("Clientes Únicos", df_tabela['CPF/CNPJ'].nunique())
            with col3:
                modelos_encontrados = len(df_tabela[df_tabela['Modelo'] != 'Modelo não encontrado'])
                st.metric("Modelos Encontrados", f"{modelos_encontrados}/{len(df_tabela)}")
            
            st.subheader("📋 Tabela de Terminais Vinculados por Cliente")
            st.dataframe(df_tabela, use_container_width=True, hide_index=True)

            # Botão de download
            csv = df_tabela.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="⬇️ Baixar Tabela (CSV)",
                data=csv,
                file_name="vinculos_clientes_terminais.csv",
                mime="text/csv"
            )

            if st.checkbox("📄 Mostrar Estrutura JSON"):
                st.subheader("Estrutura de Vínculos (Formato JSON)")
                st.json(dados_json)
        else:
            st.error("❌ Não foram encontrados vínculos válidos entre os ficheiros.")
            st.info("""
            **Possíveis causas:**
            - As planilhas não contêm dados na estrutura esperada
            - Os cabeçalhos estão em linhas diferentes da 12ª linha (header=11)
            - Os nomes das colunas são diferentes do esperado
            - Os dados estão em formato diferente
            
            **Sugestões:**
            - Ative o modo debug acima para ver detalhes do processamento
            - Verifique se os arquivos são os relatórios corretos da Etrac
            - Confirme se os dados começam na linha 12 (após cabeçalhos)
            """)

    except Exception as e:
        st.error(f"💥 Erro ao processar os ficheiros: {e}")
        st.exception(e)
else:
    st.info("📁 Por favor, carregue ambos os ficheiros para iniciar a análise.")
    
    # Instruções de uso
    with st.expander("📖 Instruções de Uso"):
        st.markdown("""
        ### Como usar esta ferramenta:
        
        1. **Arquivo de Clientes**: Deve conter as colunas:
           - Nome do Cliente / Razão Social
           - CPF/CNPJ
           - Tipo Cliente (Física/Jurídica)
           - Terminal/Frota
           - Rastreador
        
        2. **Arquivo de Rastreadores**: Deve conter as colunas:
           - Nº Série / Serial
           - Modelo
        
        3. **Formato**: Ambos os arquivos devem ser Excel (.xlsx) com dados começando na linha 12
        
        4. **Resultado**: A ferramenta irá vincular os terminais aos clientes e mostrar o modelo de cada rastreador
        """)
