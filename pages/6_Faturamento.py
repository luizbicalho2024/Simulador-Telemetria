# pages/6_Faturamento.py
import streamlit as st
import pandas as pd
from datetime import datetime
import io
import user_management_db as umdb
from fpdf import FPDF

# --- 1. CONFIGURAÇÃO E AUTENTICAÇÃO ---
st.set_page_config(
    layout="wide",
    page_title="Assistente de Faturamento",
    page_icon="💲"
)

if not st.session_state.get("authentication_status"):
    st.error("🔒 Acesso Negado! Por favor, faça login para visualizar esta página.")
    st.stop()

# --- 2. FUNÇÕES AUXILIARES ---
@st.cache_data
def processar_planilha_faturamento(uploaded_file, valor_gprs, valor_satelital):
    """
    Lê a planilha, extrai informações, classifica, calcula e retorna os dataframes de faturamento.
    """
    # Lê as primeiras 11 linhas para extrair informações do cabeçalho
    header_info = pd.read_excel(uploaded_file, header=None, nrows=11, engine='openpyxl')
    
    periodo_relatorio = "Período não identificado"
    report_month, report_year = datetime.now().month, datetime.now().year
    if len(header_info.columns) > 8:
        data_inicio_raw = header_info.iloc[8, 8]
        data_fim_raw = header_info.iloc[9, 8]
        try:
            dt_inicio = pd.to_datetime(data_inicio_raw)
            report_month = dt_inicio.month
            report_year = dt_inicio.year
            data_fim = pd.to_datetime(data_fim_raw).strftime('%d/%m/%Y')
            periodo_relatorio = f"{dt_inicio.strftime('%d/%m/%Y')} a {data_fim}"
        except Exception:
            periodo_relatorio = f"{header_info.iloc[8, 8]} a {header_info.iloc[9, 8]}"

    # Lê a tabela de dados principal
    df = pd.read_excel(uploaded_file, header=11, engine='openpyxl', dtype={'Equipamento': str})
    df = df.rename(columns={'Suspenso Dias Mês': 'Suspenso Dias Mes', 'Equipamento': 'Nº Equipamento'})

    required_cols = ['Cliente', 'Terminal', 'Data Ativação', 'Data Desativação', 'Dias Ativos Mês', 'Suspenso Dias Mes', 'Nº Equipamento', 'Condição']
    if not all(col in df.columns for col in required_cols):
        return None, None, None, None, None, "Erro de Colunas: Verifique o cabeçalho na linha 12."

    nome_cliente = "Cliente não identificado"
    if not df.empty and 'Cliente' in df.columns and pd.notna(df['Cliente'].iloc[0]):
        nome_cliente = str(df['Cliente'].iloc[0]).strip()
            
    df.dropna(subset=['Terminal'], inplace=True)
    df['Terminal'] = df['Terminal'].astype(str).str.strip()
    df['Data Ativação'] = pd.to_datetime(df['Data Ativação'], errors='coerce')
    df['Data Desativação'] = pd.to_datetime(df['Data Desativação'], errors='coerce')
    df['Dias Ativos Mês'] = pd.to_numeric(df['Dias Ativos Mês'], errors='coerce').fillna(0)
    df['Suspenso Dias Mes'] = pd.to_numeric(df['Suspenso Dias Mes'], errors='coerce').fillna(0)

    df['Tipo'] = df['Nº Equipamento'].apply(lambda x: 'Satelital' if len(str(x).strip()) == 8 else 'GPRS')
    df['Valor Unitario'] = df['Tipo'].apply(lambda x: valor_satelital if x == 'Satelital' else valor_gprs)

    dias_no_mes = pd.Timestamp(year=report_year, month=report_month, day=1).days_in_month

    # Separa os desativados primeiro
    df_desativados = df[df['Data Desativação'].notna()].copy()
    df_desativados['Dias a Faturar'] = (df_desativados['Data Desativação'].dt.day - df_desativados['Suspenso Dias Mes']).clip(lower=0)
    df_desativados['Valor a Faturar'] = (df_desativados['Valor Unitario'] / dias_no_mes) * df_desativados['Dias a Faturar']
    
    # Pega os restantes para analisar
    df_restantes = df[df['Data Desativação'].isna()].copy()
    
    # Separa os ativados no mês
    df_ativados = df_restantes[
        (df_restantes['Condição'] == 'Ativado') &
        (df_restantes['Data Ativação'].dt.month == report_month) &
        (df_restantes['Data Ativação'].dt.year == report_year)
    ].copy()
    df_ativados['Dias a Faturar'] = ((dias_no_mes - df_ativados['Data Ativação'].dt.day + 1) - df_ativados['Suspenso Dias Mes']).clip(lower=0)
    df_ativados['Valor a Faturar'] = (df_ativados['Valor Unitario'] / dias_no_mes) * df_ativados['Dias a Faturar']
    
    # O que sobrou é faturamento cheio
    df_cheio = df_restantes.drop(df_ativados.index).copy()
    df_cheio['Dias a Faturar'] = (df_cheio['Dias Ativos Mês'] - df_cheio['Suspenso Dias Mes']).clip(lower=0)
    df_cheio['Valor a Faturar'] = (df_cheio['Valor Unitario'] / dias_no_mes) * df_cheio['Dias a Faturar']
    
    return nome_cliente, periodo_relatorio, df_cheio, df_ativados, df_desativados, None

@st.cache_data
def to_excel(df_cheio, df_ativados, df_desativados):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_cheio.to_excel(writer, index=False, sheet_name='Faturamento Cheio')
        df_ativados.to_excel(writer, index=False, sheet_name='Proporcional - Ativados')
        df_desativados.to_excel(writer, index=False, sheet_name='Proporcional - Desativados')
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
pricing_config = umdb.get_pricing_config()
default_gprs = float(pricing_config.get("PRECOS_PF", {}).get("GPRS / Gsm", 0.0))
default_satelital = float(pricing_config.get("PLANOS_PJ", {}).get("36 Meses", {}).get("Satélite", 0.0))
valor_gprs = st.sidebar.number_input("Valor Unitário Mensal (GPRS)", min_value=0.0, value=default_gprs, step=1.0, format="%.2f")
valor_satelital = st.sidebar.number_input("Valor Unitário Mensal (Satelital)", min_value=0.0, value=default_satelital, step=1.0, format="%.2f")

# --- 5. UPLOAD DO FICHEIRO ---
st.subheader("Carregamento do Relatório de Terminais")
st.info("Por favor, carregue o ficheiro `relatorio_terminal_xx-xx-xxxx_xx-xx-xxxx.xlsx` exportado do sistema.")
uploaded_file = st.file_uploader("Selecione o relatório", type=['xlsx'])
st.markdown("---")

# --- 6. ANÁLISE E EXIBIÇÃO ---
if uploaded_file:
    if valor_gprs == 0.0 or valor_satelital == 0.0:
        st.warning("Por favor, insira os valores unitários de GPRS e Satelital na barra lateral para continuar.")
    else:
        try:
            nome_cliente, periodo_relatorio, df_cheio, df_ativados, df_desativados, error_message = processar_planilha_faturamento(uploaded_file, valor_gprs, valor_satelital)
            
            if error_message:
                st.error(error_message)
            elif df_cheio is not None:
                total_faturamento_cheio = df_cheio['Valor a Faturar'].sum()
                total_faturamento_ativados = df_ativados['Valor a Faturar'].sum()
                total_faturamento_desativados = df_desativados['Valor a Faturar'].sum()
                faturamento_proporcional_total = total_faturamento_ativados + total_faturamento_desativados
                faturamento_total_geral = total_faturamento_cheio + faturamento_proporcional_total

                st.header("Resumo do Faturamento")
                st.subheader(f"Cliente: {nome_cliente}")
                st.caption(f"Período: {periodo_relatorio}")
                
                df_total = pd.concat([df_cheio, df_ativados, df_desativados])
                total_gprs = len(df_total[df_total['Tipo'] == 'GPRS'])
                total_satelital = len(df_total[df_total['Tipo'] == 'Satelital'])
                
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Nº Fat. Cheio", value=len(df_cheio))
                col2.metric("Nº Fat. Proporcional", value=len(df_ativados) + len(df_desativados))
                col3.metric("Total GPRS", value=total_gprs)
                col4.metric("Total Satelitais", value=total_satelital)
                
                col_a, col_b, col_c = st.columns(3)
                col_a.success(f"**Faturamento (Cheio):** R$ {total_faturamento_cheio:,.2f}")
                col_b.warning(f"**Faturamento (Proporcional):** R$ {faturamento_proporcional_total:,.2f}")
                col_c.info(f"**FATURAMENTO TOTAL:** R$ {faturamento_total_geral:,.2f}")

                st.markdown("---")
                
                st.subheader("Ações Finais")
                excel_data = to_excel(df_cheio, df_ativados, df_desativados)
                faturamento_data_log = {
                    "cliente": nome_cliente, "periodo_relatorio": periodo_relatorio,
                    "valor_total": faturamento_total_geral, "terminais_cheio": len(df_cheio),
                    "terminais_proporcional": len(df_ativados) + len(df_desativados),
                    "terminais_gprs": total_gprs, "terminais_satelitais": total_satelital,
                    "valor_unitario_gprs": valor_gprs, "valor_unitario_satelital": valor_satelital
                }

                st.download_button(
                   label="📥 Exportar e Salvar Histórico (.xlsx)",
                   data=excel_data,
                   file_name=f"Faturamento_{nome_cliente.replace(' ', '_')}_{datetime.now().strftime('%Y-%m')}.xlsx",
                   mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                   on_click=umdb.log_faturamento, args=(faturamento_data_log,)
                )

                st.markdown("---")

                with st.expander("Detalhamento do Faturamento Proporcional (Ativações no Mês)"):
                    if not df_ativados.empty:
                        st.dataframe(
                            df_ativados[['Terminal', 'Nº Equipamento', 'Placa', 'Tipo', 'Data Ativação', 'Dias Ativos Mês', 'Suspenso Dias Mes', 'Dias a Faturar', 'Valor Unitario', 'Valor a Faturar']],
                            use_container_width=True, hide_index=True,
                            column_config={
                                "Data Ativação": st.column_config.DatetimeColumn("Data Ativação", format="DD/MM/YYYY"),
                                "Valor Unitario": st.column_config.NumberColumn("Valor Mensal Cheio (R$)", format="R$ %.2f"),
                                "Valor a Faturar": st.column_config.NumberColumn("Valor a Faturar (R$)", format="R$ %.2f")
                            }
                        )
                    else:
                        st.info("Nenhum terminal ativado com faturamento proporcional neste período.")
                
                with st.expander("Detalhamento do Faturamento Proporcional (Desativações no Mês)"):
                    if not df_desativados.empty:
                        st.dataframe(
                            df_desativados[['Terminal', 'Nº Equipamento', 'Placa', 'Tipo', 'Data Desativação', 'Dias Ativos Mês', 'Suspenso Dias Mes', 'Dias a Faturar', 'Valor Unitario', 'Valor a Faturar']],
                            use_container_width=True, hide_index=True,
                            column_config={
                                "Data Desativação": st.column_config.DatetimeColumn("Data Desativação", format="DD/MM/YYYY"),
                                "Valor Unitario": st.column_config.NumberColumn("Valor Mensal Cheio (R$)", format="R$ %.2f"),
                                "Valor a Faturar": st.column_config.NumberColumn("Valor a Faturar (R$)", format="R$ %.2f")
                            }
                        )
                    else:
                        st.info("Nenhum terminal desativado neste período.")
                
                with st.expander("Detalhamento do Faturamento Cheio"):
                    if not df_cheio.empty:
                        st.dataframe(
                            df_cheio[['Terminal', 'Nº Equipamento', 'Placa', 'Tipo', 'Valor a Faturar']],
                            use_container_width=True, hide_index=True,
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
