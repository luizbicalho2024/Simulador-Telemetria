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

# --- 2. FUNÇÃO AUXILIAR ROBUSTA ---
@st.cache_data
def processar_vinculos(file_clientes, file_rastreadores):
    """
    Lê as duas planilhas, processa a estrutura aninhada dos clientes e
    junta com as informações de modelo dos rastreadores.
    Retorna:
        - DataFrame tabular para exibição
        - Estrutura JSON agrupada por cliente
    """
    try:
        # Etapa 1: Preparar o mapa de Rastreador -> Modelo
        df_rastreadores = pd.read_excel(file_rastreadores, header=11, engine="openpyxl")
        df_rastreadores.columns = df_rastreadores.columns.str.strip()
        df_rastreadores = df_rastreadores.rename(
            columns={"Nº Série": "Rastreador", "Modelo": "Modelo_Rastreador"}
        )
        df_rastreadores.dropna(subset=["Rastreador"], inplace=True)

        # Normaliza chave Rastreador
        df_rastreadores["Rastreador"] = (
            df_rastreadores["Rastreador"].astype(str).str.replace(r"\.0$", "", regex=True)
        )
        mapa_modelos = df_rastreadores.set_index("Rastreador")["Modelo_Rastreador"].to_dict()

        # Etapa 2: Ler e processar a planilha de clientes
        df_clientes_raw = pd.read_excel(file_clientes, header=11, engine="openpyxl")
        df_clientes_raw.columns = df_clientes_raw.columns.str.strip()

        # Remove colunas completamente vazias
        df_clientes_raw = df_clientes_raw.loc[:, ~df_clientes_raw.columns.str.contains("^Unnamed", na=False)]
        df_clientes_raw.dropna(how="all", inplace=True)

        registros_consolidados = []
        cliente_atual = {}

        for _, row in df_clientes_raw.iterrows():
            tipo_cliente = str(row.get("Tipo Cliente", "")).strip()

            # Detecta início de bloco de cliente
            if "Jurídica" in tipo_cliente or "Física" in tipo_cliente:
                cliente_atual = {
                    "Nome do Cliente": row.get("Nome do Cliente"),
                    "CPF/CNPJ": row.get("CPF/CNPJ"),
                    "Tipo Cliente": tipo_cliente,
                }
                if pd.isna(row.get("Terminal")):
                    continue

            # Detecta linha de terminal vinculada
            if (
                pd.notna(row.get("Terminal"))
                and cliente_atual
                and str(row.get("Terminal")).strip().lower() != "terminal"
            ):
                registros_consolidados.append({
                    **cliente_atual,
                    "Terminal/Frota": row.get("Terminal"),
                    "Rastreador": str(row.get("Rastreador")).replace(".0", ""),
                })

        if not registros_consolidados:
            return None, None

        # Etapa 3: DataFrame final e cruzamento
        df_final = pd.DataFrame(registros_consolidados)
        df_final["Modelo"] = df_final["Rastreador"].map(mapa_modelos).fillna("Modelo não encontrado")

        # Etapa 4: Agrupar para JSON estruturado
        df_grouped = df_final.groupby(["Nome do Cliente", "CPF/CNPJ", "Tipo Cliente"]).apply(
            lambda x: x[["Terminal/Frota", "Rastreador", "Modelo"]].to_dict("records")
        ).reset_index(name="Terminais")

        json_resultado = json.loads(df_grouped.to_json(orient="records", force_ascii=False))

        return df_final[["Nome do Cliente", "CPF/CNPJ", "Tipo Cliente", "Terminal/Frota", "Rastreador", "Modelo"]], json_resultado

    except Exception as e:
        raise RuntimeError(f"Erro ao processar os ficheiros: {e}")

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
    uploaded_clientes = st.file_uploader("Carregue o `relatorio_clientes.xlsx`", type=["xlsx"], key="clientes_upload")

with col2:
    st.info("**2. Relatório de Rastreadores (Estoque)**")
    uploaded_rastreadores = st.file_uploader("Carregue o `relatorio_rastreador.xlsx`", type=["xlsx"], key="rastreadores_upload")

st.markdown("---")

# --- 5. ANÁLISE E EXIBIÇÃO ---
if uploaded_clientes and uploaded_rastreadores:
    try:
        with st.spinner("⏳ Processando e comparando as planilhas..."):
            df_tabela, dados_json = processar_vinculos(uploaded_clientes, uploaded_rastreadores)

        if df_tabela is not None and not df_tabela.empty:
            st.success(f"✅ Análise concluída! Foram encontrados **{len(df_tabela)}** terminais vinculados a clientes.")

            st.subheader("📊 Tabela de Terminais Vinculados por Cliente")
            st.dataframe(df_tabela, use_container_width=True, hide_index=True)

            st.subheader("📝 Estrutura de Vínculos (Formato JSON)")
            st.json(dados_json)

            # Botão para download do JSON
            json_str = json.dumps(dados_json, ensure_ascii=False, indent=4)
            st.download_button(
                label="⬇️ Baixar JSON",
                data=json_str,
                file_name="vinculos_clientes_terminais.json",
                mime="application/json"
            )

        else:
            st.warning("⚠️ Não foram encontrados vínculos válidos. Verifique se os ficheiros têm os dados esperados.")

    except Exception as e:
        st.error(str(e))
        st.info("Por favor, verifique se os ficheiros têm o formato e as colunas esperadas.")
else:
    st.info("📌 Por favor, carregue ambos os ficheiros para iniciar a análise.")
