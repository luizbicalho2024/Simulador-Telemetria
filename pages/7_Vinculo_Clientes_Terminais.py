import streamlit as st
import pandas as pd
import json

st.set_page_config(page_title="Relacionamento de Planilhas", layout="wide")

st.title("🔗 Relacionamento de Clientes x Rastreadores")

# Upload das planilhas
clientes_file = st.file_uploader("📂 Envie a planilha de Clientes (relatorio_clientes.xlsx)", type=["xlsx"])
rastreador_file = st.file_uploader("📂 Envie a planilha de Rastreadores (relatorio_rastreador.xlsx)", type=["xlsx"])

if clientes_file and rastreador_file:
    # Carregar planilhas
    clientes_df = pd.read_excel(clientes_file)
    rastreador_df = pd.read_excel(rastreador_file)

    # Normalizar nomes das colunas (remove espaços extras e uniformiza)
    clientes_df.columns = clientes_df.columns.str.strip()
    rastreador_df.columns = rastreador_df.columns.str.strip()

    st.subheader("📑 Colunas detectadas")
    st.write("**Clientes:**", clientes_df.columns.tolist())
    st.write("**Rastreadores:**", rastreador_df.columns.tolist())

    # 🚨 Ajuste manual: edite aqui se os nomes forem diferentes nas suas planilhas
    col_nome = "Nome do Cliente"
    col_cpf = "CPF/CNPJ"
    col_tipo = "Tipo Cliente"
    col_terminal_frota = "Terminal/Frota"

    col_terminal = "Terminal"
    col_rastreador = "Rastreador"
    col_modelo = "Modelo do Rastreador"

    try:
        # Fazer merge
        merged = pd.merge(
            clientes_df,
            rastreador_df,
            left_on=col_terminal_frota,
            right_on=col_terminal,
            how="inner"
        )

        # Selecionar apenas colunas necessárias
        resultado = merged[[
            col_nome,
            col_cpf,
            col_tipo,
            col_terminal_frota,
            col_rastreador,
            col_modelo
        ]]

        st.subheader("📊 Resultado da Junção")
        st.dataframe(resultado, use_container_width=True)

        # Converter para JSON
        resultado_json = resultado.to_dict(orient="records")
        st.subheader("📝 JSON Gerado")
        st.json(resultado_json)

        # Download JSON
        json_str = json.dumps(resultado_json, ensure_ascii=False, indent=4)
        st.download_button(
            label="⬇️ Baixar JSON",
            data=json_str,
            file_name="relacionamento.json",
            mime="application/json"
        )

    except KeyError as e:
        st.error(f"⚠️ Erro: {e}. Verifique os nomes das colunas e ajuste no script.")
