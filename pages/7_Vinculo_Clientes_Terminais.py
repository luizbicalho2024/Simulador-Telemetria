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
        
        # Tentar diferentes variações de nomes de coluna
        coluna_serie = None
        coluna_modelo = None
        
        for col in df_rastreadores.columns:
            col_lower = str(col).lower().strip()
            if any(term in col_lower for term in ['série', 'serie', 'nº série', 'n série', 'serial']):
                coluna_serie = col
            elif any(term in col_lower for term in ['modelo', 'model']):
                coluna_modelo = col
        
        if not coluna_serie or not coluna_modelo:
            st.error(f"❌ Colunas necessárias não encontradas. Série: {coluna_serie}, Modelo: {coluna_modelo}")
            return None, None
            
        df_rastreadores = df_rastreadores.rename(columns={coluna_serie: 'Rastreador', coluna_modelo: 'Modelo_Rastreador'})
        df_rastreadores.dropna(subset=['Rastreador'], inplace=True)
        
        # Limpar dados de rastreadores
        df_rastreadores['Rastreador'] = df_rastreadores['Rastreador'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
        mapa_modelos = df_rastreadores.set_index('Rastreador')['Modelo_Rastreador'].to_dict()
        
        st.write(f"✅ **Debug:** {len(mapa_modelos)} rastreadores carregados")

        # === ETAPA 2: PROCESSAR ARQUIVO DE CLIENTES ===
        st.write("🔍 **Debug:** Processando arquivo de clientes...")
        df_clientes_raw = pd.read_excel(file_clientes, header=11, engine='openpyxl')
        
        # Debug: Mostrar colunas e primeiras linhas
        st.write(f"📊 Colunas encontradas no arquivo de clientes: {list(df_clientes_raw.columns)}")
        st.write("📋 **Debug:** Primeiras 5 linhas do arquivo de clientes:")
        st.dataframe(df_clientes_raw.head())
        
        # Remove colunas completamente vazias
        df_clientes_raw = df_clientes_raw.loc[:, ~df_clientes_raw.columns.str.contains('^Unnamed', na=False)]
        df_clientes_raw.dropna(how='all', inplace=True)
        
        # Identificar colunas dinamicamente
        colunas_mapeadas = {}
        for col in df_clientes_raw.columns:
            col_lower = str(col).lower().strip()
            if any(term in col_lower for term in ['nome', 'cliente', 'razão social']):
                colunas_mapeadas['nome'] = col
            elif any(term in col_lower for term in ['cpf', 'cnpj', 'documento']):
                colunas_mapeadas['documento'] = col
            elif any(term in col_lower for term in ['tipo', 'pessoa']):
                colunas_mapeadas['tipo'] = col
            elif any(term in col_lower for term in ['terminal', 'frota']):
                colunas_mapeadas['terminal'] = col
            elif any(term in col_lower for term in ['rastreador', 'equipamento', 'série']):
                colunas_mapeadas['rastreador'] = col
        
        st.write(f"🗂️ **Debug:** Colunas mapeadas: {colunas_mapeadas}")
        
        if not all(key in colunas_mapeadas for key in ['nome', 'documento', 'tipo', 'terminal', 'rastreador']):
            st.error("❌ Nem todas as colunas necessárias foram encontradas!")
            return None, None

        # === ETAPA 3: PROCESSAR REGISTROS ===
        registos_consolidados = []
        cliente_atual = {}
        linhas_processadas = 0
        clientes_encontrados = 0
        terminais_encontrados = 0

        for index, row in df_clientes_raw.iterrows():
            linhas_processadas += 1
            
            # Obter valores das colunas mapeadas
            nome_cliente = row.get(colunas_mapeadas['nome'], '')
            documento = row.get(colunas_mapeadas['documento'], '')
            tipo_cliente = str(row.get(colunas_mapeadas['tipo'], '')).strip()
            terminal = row.get(colunas_mapeadas['terminal'], '')
            rastreador = row.get(colunas_mapeadas['rastreador'], '')
            
            # Identificar linha de cliente
            if (tipo_cliente and ('Jurídica' in tipo_cliente or 'Física' in tipo_cliente)) or \
               (pd.notna(nome_cliente) and pd.notna(documento) and 
                str(nome_cliente).strip() != '' and str(documento).strip() != ''):
                
                cliente_atual = {
                    'Nome do Cliente': nome_cliente,
                    'CPF/CNPJ': documento,
                    'Tipo Cliente': tipo_cliente if tipo_cliente else 'Não especificado'
                }
                clientes_encontrados += 1
                
                # Se a mesma linha tem terminal, processar
                if pd.notna(terminal) and pd.notna(rastreador) and \
                   str(terminal).strip() != '' and str(rastreador).strip() != '' and \
                   str(terminal).strip().lower() != 'terminal':
                    
                    registos_consolidados.append({
                        **cliente_atual,
                        'Terminal/Frota': str(terminal).strip(),
                        'Rastreador': str(rastreador).replace('.0', '').strip()
                    })
                    terminais_encontrados += 1
            
            # Processar linha de terminal (quando cliente já foi definido)
            elif cliente_atual and pd.notna(terminal) and pd.notna(rastreador) and \
                 str(terminal).strip() != '' and str(rastreador).strip() != '' and \
                 str(terminal).strip().lower() != 'terminal':
                
                registos_consolidados.append({
                    **cliente_atual,
                    'Terminal/Frota': str(terminal).strip(),
                    'Rastreador': str(rastreador).replace('.0', '').strip()
                })
                terminais_encontrados += 1

        # Debug final
        st.write(f"📈 **Debug:** Processadas {linhas_processadas} linhas")
        st.write(f"👥 **Debug:** {clientes_encontrados} clientes identificados")
        st.write(f"📱 **Debug:** {terminais_encontrados} terminais encontrados")
        st.write(f"🔗 **Debug:** {len(registos_consolidados)} vínculos consolidados")

        if not registos_consolidados:
            st.error("❌ Nenhum vínculo foi consolidado. Verifique a estrutura dos dados.")
            return None, None

        # === ETAPA 4: CRIAR DATAFRAME FINAL ===
        df_final = pd.DataFrame(registos_consolidados)
        df_final['Modelo'] = df_final['Rastreador'].map(mapa_modelos).fillna('Modelo não encontrado')
        
        # Debug: Verificar rastreadores não encontrados
        rastreadores_nao_encontrados = df_final[df_final['Modelo'] == 'Modelo não encontrado']['Rastreador'].unique()
        if len(rastreadores_nao_encontrados) > 0:
            st.warning(f"⚠️ **Debug:** {len(rastreadores_nao_encontrados)} rastreadores sem modelo: {list(rastreadores_nao_encontrados)[:10]}")
        
        # === ETAPA 5: AGRUPAR PARA JSON ===
        df_grouped = df_final.groupby(['Nome do Cliente', 'CPF/CNPJ', 'Tipo Cliente']).apply(
            lambda x: x[['Terminal/Frota', 'Rastreador', 'Modelo']].to_dict('records')
        ).reset_index(name='Terminais')

        json_resultado = json.loads(df_grouped.to_json(orient="records", force_ascii=False))

        return df_final[['Nome do Cliente', 'CPF/CNPJ', 'Tipo Cliente', 'Terminal/Frota', 'Rastreador', 'Modelo']], json_resultado

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
except: pass

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
                # Versão sem debug para produção
                @st.cache_data
                def processar_vinculos_prod(file_clientes, file_rastreadores):
                    # Versão simplificada sem st.write para debug
                    # [Implementar versão limpa aqui se necessário]
                    pass
        
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
