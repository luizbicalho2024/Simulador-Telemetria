# pages/Faturamento.py
import streamlit as st
import pandas as pd
from datetime import datetime
import io
import user_management_db as umdb

# --- 1. CONFIGURAÇÃO E AUTENTICAÇÃO ---
st.set_page_config(layout="wide", page_title="Assistente de Faturamento", icon="💲")

if not st.session_state.get("authentication_status"):
    st.error("🔒 Acesso Negado!"); st.stop()

# --- 2. FUNÇÕES AUXILIARES ---
@st.cache_data
def processar_planilha_faturamento(uploaded_file, valor_gprs, valor_satelital):
    df = pd.read_excel(uploaded_file, header=11, engine='openpyxl', dtype={'Equipamento': str})
    df = df.rename(columns={'Suspenso Dias Mês': 'Suspenso Dias Mes', 'Equipamento': 'Nº Equipamento'})
    
    required_cols = ['Cliente', 'Terminal', 'Data Desativação', 'Dias Ativos Mês', 'Suspenso Dias Mes', 'Nº Equipamento']
    if not all(col in df.columns for col in required_cols):
        return None, None, None, "Erro de Colunas: Verifique o cabeçalho na linha 12."
    
    nome_cliente = "Cliente não identificado"
    if not df.empty and 'Cliente' in df.columns:
        first_valid_client = df['Cliente'].dropna().iloc[0]
        if pd.notna(first_valid_client):
            nome_cliente = str(first_valid_client).strip()
            
    df.dropna(subset=['Terminal'], inplace=True)
    df['Terminal'] = df['Terminal'].astype(str).str.strip()
    df['Data Desativação'] = pd.to_datetime(df['Data Desativação'], errors='coerce')
    df['Dias Ativos Mês'] = pd.to_numeric(df['Dias Ativos Mês'], errors='coerce').fillna(0)
    df['Suspenso Dias Mes'] = pd.to_numeric(df['Suspenso Dias Mes'], errors='coerce').fillna(0)

    df['Tipo'] = df['Nº Equipamento'].apply(lambda x: 'Satelital' if len(str(x).strip()) == 8 else 'GPRS')
    df['Valor Unitario'] = df['Tipo'].apply(lambda x: valor_satelital if x == 'Satelital' else valor_gprs)

    dias_no_mes = pd.Timestamp(datetime.now()).days_in_month
    df['Dias a Faturar'] = (df['Dias Ativos Mês'] - df['Suspenso Dias Mes']).clip(lower=0)
    df['Valor a Faturar'] = (df['Valor Unitario'] / dias_no_mes) * df['Dias a Faturar']
    
    df_faturamento_cheio = df[df['Dias a Faturar'] >= dias_no_mes]
    df_faturamento_proporcional = df[df['Dias a Faturar'] < dias_no_mes]
    
    return nome_cliente, df_faturamento_cheio, df_faturamento_proporcional, None

@st.cache_data
def to_excel(df_cheio, df_proporcional):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_cheio.to_excel(writer, index=False, sheet_name='Faturamento Cheio')
        df_proporcional.to_excel(writer, index=False, sheet_name='Faturamento Proporcional')
    return output.getvalue()

# --- 3. INTERFACE DA PÁGINA ---
st.sidebar.image("imgs/v-c.png", width=120)
st.sidebar.title(f"Olá, {st.session_state.get('name', 'N/A')}! 👋")
st.sidebar.markdown("---")

try:
    st.image("imgs/logo.png", width=250)
except: pass

st.markdown("<h1 style='text-align: center; color: #006494;'>💲 Assistente de Faturamento</h1>", unsafe_allow_html=True)
st.markdown("---")

# --- 4. INPUTS DE CONFIGURAÇÃO ---
st.sidebar.header("Valores de Faturamento")
valor_gprs = st.sidebar.number_input("Valor Unitário Mensal (GPRS)", min_value=0.0, step=1.0, format="%.2f")
valor_satelital = st.sidebar.number_input("Valor Unitário Mensal (Satelital)", min_value=0.0, step=1.0, format="%.2f")

# --- 5. UPLOAD DO FICHEIRO ---
st.subheader("Carregamento do Relatório de Terminais")
st.info("Por favor, carregue o ficheiro `relatorio_terminal_xx-xx-xxxx_xx-xx-xxxx.xlsx` exportado do sistema.")

# Input para o período do relatório
periodo_relatorio = st.text_input("Período do Relatório (ex: 01/08/2025 a 31/08/2025)", key="faturamento_periodo")
uploaded_file = st.file_uploader("Selecione o relatório", type=['xlsx'])

st.markdown("---")

# --- 6. ANÁLISE E EXIBIÇÃO ---
if uploaded_file:
    if valor_gprs == 0.0 or valor_satelital == 0.0:
        st.warning("Por favor, insira os valores unitários de GPRS e Satelital na barra lateral para continuar.")
    elif not periodo_relatorio:
        st.warning("Por favor, insira o período do relatório.")
    else:
        try:
            nome_cliente, df_cheio, df_proporcional, error_message = processar_planilha_faturamento(uploaded_file, valor_gprs, valor_satelital)
            
            if error_message:
                st.error(error_message)
            elif df_cheio is not None:
                total_faturamento_cheio = df_cheio['Valor a Faturar'].sum()
                total_faturamento_proporcional = df_proporcional['Valor a Faturar'].sum()
                faturamento_total_geral = total_faturamento_cheio + total_faturamento_proporcional

                st.header("Resumo do Faturamento")
                st.subheader(f"Cliente: {nome_cliente}")
                st.caption(f"Período: {periodo_relatorio}")

                total_gprs = len(df_cheio[df_cheio['Tipo'] == 'GPRS']) + len(df_proporcional[df_proporcional['Tipo'] == 'GPRS'])
                total_satelital = len(df_cheio[df_cheio['Tipo'] == 'Satelital']) + len(df_proporcional[df_proporcional['Tipo'] == 'Satelital'])
                
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Nº Faturamento Cheio", value=len(df_cheio))
                col2.metric("Nº Faturamento Proporcional", value=len(df_proporcional))
                col3.metric("Total Terminais GPRS", value=total_gprs)
                col4.metric("Total Terminais Satelitais", value=total_satelital)
                
                col_a, col_b, col_c = st.columns(3)
                col_a.success(f"**Faturamento (Cheio):** R$ {total_faturamento_cheio:,.2f}")
                col_b.warning(f"**Faturamento (Proporcional):** R$ {total_faturamento_proporcional:,.2f}")
                col_c.info(f"**FATURAMENTO TOTAL:** R$ {faturamento_total_geral:,.2f}")

                st.markdown("---")
                
                st.subheader("Ações Finais")
                
                excel_data = to_excel(df_cheio, df_proporcional)
                faturamento_data_log = {
                    "cliente": nome_cliente, "periodo_relatorio": periodo_relatorio,
                    "valor_total": faturamento_total_geral, "terminais_cheio": len(df_cheio),
                    "terminais_proporcional": len(df_proporcional), "terminais_gprs": total_gprs,
                    "terminais_satelitais": total_satelital
                }

                st.download_button(
                   label="📥 Exportar e Salvar Histórico (.xlsx)",
                   data=excel_data,
                   file_name=f"Faturamento_{nome_cliente.replace(' ', '_')}_{datetime.now().strftime('%Y-%m')}.xlsx",
                   mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                   on_click=umdb.log_faturamento, args=(faturamento_data_log,)
                )

                st.markdown("---")

                with st.expander("Detalhamento do Faturamento Proporcional"):
                    # ... (código da tabela como antes)
                    if not df_proporcional.empty:
                          st.dataframe(
                              df_proporcional[['Terminal', 'Nº Equipamento', 'Placa', 'Tipo', 'Data Desativação', 'Dias Ativos Mês', 'Suspenso Dias Mes', 'Dias a Faturar', 'Valor Unitario', 'Valor a Faturar']],
                              use_container_width=True,
                              hide_index=True,
                              column_config={
                                  "Data Desativação": st.column_config.DatetimeColumn("Data Desativação", format="DD/MM/YYYY"),
                                  "Valor Unitario": st.column_config.NumberColumn("Valor Mensal Cheio (R$)", format="R$ %.2f"),
                                  "Valor a Faturar": st.column_config.NumberColumn("Valor a Faturar (R$)", format="R$ %.2f")
                              }
                          )
                      else:
                          st.info("Nenhum terminal com faturamento proporcional neste período.")
                
                with st.expander("Detalhamento do Faturamento Cheio"):
                    # ... (código da tabela como antes)
                    if not df_cheio.empty:
                          st.dataframe(
                              df_cheio[['Terminal', 'Nº Equipamento', 'Placa', 'Tipo', 'Valor a Faturar']],
                              use_container_width=True,
                              hide_index=True,
                              column_config={
                                  "Valor a Faturar": st.column_config.NumberColumn("Valor Faturado (R$)", format="R$ %.2f")
                              }
                          )
                      else:
                          st.info("Nenhum terminal com faturamento cheio neste período.")  

        except Exception as e:
            st.error(f"Ocorreu um erro ao processar o ficheiro: {e}")
            st.info("Por favor, verifique se o ficheiro tem o formato e as colunas esperadas.")
else:
    st.info("Aguardando o carregamento do relatório para iniciar a análise.")
