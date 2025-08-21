import streamlit as st
import pandas as pd
import unidecode

st.set_page_config(page_title="Relacionar Planilhas", layout="wide")

st.title("📊 Relacionar Planilhas de Clientes e Rastreadores")

st.write("Carregue os arquivos **relatorio_clientes.xlsx** e **relatorio_rastreador.xlsx**")

# Upload dos arquivos
clientes_file = st.file_uploader("Carregar planilha de clientes", type=["xlsx"])
rastreadores_file = st.file_uploader("Carregar planilha de rastreadores", type=["xlsx"])

if clientes_file and rastreadores_file:
    # Carregar planilhas
    clientes = pd.read_excel(clientes_file)
    rastreadores = pd.read_excel(rastreadores_file)

    # Função para normalizar nomes de colunas
    def normalize_columns(df):
        df.columns = [
            unidecode.unidecode(col).strip().lower().replace(" ", "_")
            for col in df.columns
        ]
        return df

    # Normalizar colunas
    clientes = normalize_columns(clientes)
    rastreadores = normalize_columns(rastreadores)

    st.subheader("🔍 Prévia - Planilha de Clientes")
    st.dataframe(clientes.head())

    st.subheader("🔍 Prévia - Planilha de Rastreadores")
    st.dataframe(rastreadores.head())

    # Normalizar colunas-chave (forçando para string)
    if "terminal" in clientes.columns and "terminal" in rastreadores.columns:
        clientes["terminal"] = clientes["terminal"].astype(str).str.strip()
        rastreadores["terminal"] = rastreadores["terminal"].astype(str).str.strip()

        # Merge
        resultado = pd.merge(
            clientes,
            rastreadores,
            on="terminal",
            how="inner",
            suffixes=("_cliente", "_rastreador")
        )

        if not resultado.empty:
            # Selecionar colunas relevantes (ajuste conforme os nomes reais da sua planilha)
            colunas_desejadas = [
                "nome_do_cliente", "cpf_cnpj", "tipo_cliente",
                "terminal", "frota", "rastreador", "modelo_do_rastreador"
            ]
            # Filtrar apenas colunas que realmente existem no DF
            colunas_existentes = [c for c in colunas_desejadas if c in resultado.columns]
            resultado_final = resultado[colunas_existentes]

            st.subheader("✅ Resultado da Relação")
            st.dataframe(resultado_final)

            # Exportar como JSON
            st.download_button(
                "📥 Baixar JSON",
                resultado_final.to_json(orient="records", force_ascii=False, indent=4),
                file_name="resultado.json",
                mime="application/json"
            )

            # Exportar como Excel
            st.download_button(
                "📥 Baixar Excel",
                resultado_final.to_excel(index=False, engine="openpyxl"),
                file_name="resultado.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.warning("⚠️ Não foram encontrados vínculos válidos entre as planilhas. "
                       "Verifique se os valores da coluna **terminal** realmente existem nas duas.")
    else:
        st.error("❌ A coluna 'terminal' não foi encontrada em uma ou ambas as planilhas.")
