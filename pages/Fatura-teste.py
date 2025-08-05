# pages/Faturamento.py
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
    # Lê as primeiras 11 linhas para extrair informações do cabeçalho
    header_info = pd.read_excel(uploaded_file, header=None, nrows=11, engine='openpyxl')
    
    periodo_relatorio = "Período não identificado"
    if len(header_info.columns) > 8:
        data_inicio_raw = header_info.iloc[8, 8]
        data_fim_raw = header_info.iloc[9, 8]
        try:
            data_inicio = pd.to_datetime(data_inicio_raw).strftime('%d/%m/%Y')
            data_fim = pd.to_datetime(data_fim_raw).strftime('%d/%m/%Y')
            periodo_relatorio = f"{data_inicio} a {data_fim}"
        except Exception:
            periodo_relatorio = f"{data_inicio_raw} a {data_fim_raw}"

    # Lê a tabela de dados principal
    df = pd.read_excel(uploaded_file, header=11, engine='openpyxl', dtype={'Equipamento': str})
    df = df.rename(columns={'Suspenso Dias Mês': 'Suspenso Dias Mes', 'Equipamento': 'Nº Equipamento'})

    required_cols = ['Cliente', 'Terminal', 'Data Desativação', 'Dias Ativos Mês', 'Suspenso Dias Mes', 'Nº Equipamento']
    if not all(col in df.columns for col in required_cols):
        return None, None, None, None, "Erro de Colunas: Verifique o cabeçalho na linha 12."

    nome_cliente = "Cliente não identificado"
    if not df.empty and 'Cliente' in df.columns and pd.notna(df['Cliente'].iloc[0]):
        nome_cliente = str(df['Cliente'].iloc[0]).strip()
            
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
    
    return nome_cliente, periodo_relatorio, df_faturamento_cheio, df_faturamento_proporcional, None

@st.cache_data
def to_excel(df_cheio, df_proporcional):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_cheio.to_excel(writer, index=False, sheet_name='Faturamento Cheio')
        df_proporcional.to_excel(writer, index=False, sheet_name='Faturamento Proporcional')
    return output.getvalue()

def create_pdf_report(nome_cliente, periodo, totais, df_cheio, df_proporcional):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Resumo do Faturamento", 0, 1, "C")
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 10, f"Cliente: {nome_cliente}", 0, 1, "L")
    pdf.cell(0, 10, f"Periodo: {periodo}", 0, 1, "L")
    pdf.ln(10)

    pdf.set_font("Arial", "B", 11)
    pdf.cell(95, 8, "Faturamento (Cheio)", 1, 0, "C")
    pdf.cell(95, 8, "Faturamento (Proporcional)", 1, 1, "C")
    pdf.set_font("Arial", "", 11)
    pdf.cell(95, 8, f"R$ {totais['cheio']:,.2f}", 1, 0, "C")
    pdf.cell(95, 8, f"R$ {totais['proporcional']:,.2f}", 1, 1, "C")
    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 10, f"FATURAMENTO TOTAL: R$ {totais['geral']:,.2f}", 1, 1, "C")
    pdf.ln(10)

    def draw_table(title, df):
        if not df.empty:
            pdf.set_font("Arial", "B", 12)
            pdf.cell(0, 10, title, 0, 1, "L")
            pdf.set_font("Arial", "B", 7)
            
            col_widths = {
                'Terminal': 20, 'Nº Equipamento': 25, 'Placa': 18, 'Tipo': 15,
                'Data Desativação': 22, 'Dias Ativos Mês': 15, 'Suspenso Dias Mes': 15,
                'Dias a Faturar': 15, 'Valor Unitario': 20, 'Valor a Faturar': 25
            }
            header = [h for h in list(df.columns) if h in col_widths]
            
            for h in header:
                pdf.cell(col_widths[h], 7, h, 1, 0, 'C')
            pdf.ln()

            pdf.set_font("Arial", "", 7)
            for _, row in df.iterrows():
                for h in header:
                    cell_text = str(row[h])
                    if isinstance(row[h], datetime) and pd.notna(row[h]):
                        cell_text = row[h].strftime('%d/%m/%Y')
                    elif isinstance(row[h], float) or isinstance(row[h], int):
                        cell_text = f"R$ {row[h]:,.2f}" if 'Valor' in h else str(int(row[h]))
                    elif pd.isna(row[h]):
                        cell_text = ""
                    pdf.cell(col_widths[h], 6, cell_text, 1, 0, 'C')
                pdf.ln()
            pdf.ln(5)

    draw_table("Detalhamento do Faturamento Cheio", df_cheio[['Terminal', 'Nº Equipamento', 'Placa', 'Tipo', 'Valor a Faturar']])
    draw_table("Detalhamento do Faturamento Proporcional", df_proporcional[['Terminal', 'Nº Equipamento', 'Placa', 'Tipo', 'Data Desativação', 'Dias Ativos Mês', 'Suspenso Dias Mes', 'Dias a Faturar', 'Valor Unitario', 'Valor a Faturar']])
    
    return pdf.output(dest='S').encode('latin-1')


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

uploaded_file = st.file_uploader("Selecione o relatório", type=['xlsx'])

st.markdown("---")

# --- 6. ANÁLISE E EXIBIÇÃO ---
if uploaded_file:
    if valor_gprs == 0.0 or valor_satelital == 0.0:
        st.warning("Por favor, insira os valores unitários de GPRS e Satelital na barra lateral para continuar.")
    else:
        try:
            nome_cliente, periodo_relatorio, df_cheio, df_proporcional, error_message = processar_planilha_faturamento(uploaded_file, valor_gprs, valor_satelital)
            
            if error_message:
                st.error(error_message)
            elif df_cheio is not None:
                total_faturamento_cheio = df_cheio['Valor a Faturar'].sum()
                total_faturamento_proporcional = df_proporcional['Valor a Faturar'].sum()
                faturamento_total_geral = total_faturamento_cheio + total_faturamento_proporcional

                st.header("Resumo do Faturamento")
                st.subheader(f"Cliente: {nome_cliente}")
                st.caption(f"Período: {periodo_relatorio}")
                
                df_total = pd.concat([df_cheio, df_proporcional])
                total_gprs = len(df_total[df_total['Tipo'] == 'GPRS'])
                total_satelital = len(df_total[df_total['Tipo'] == 'Satelital'])
                
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
                totais_pdf = {"cheio": total_faturamento_cheio, "proporcional": total_faturamento_proporcional, "geral": faturamento_total_geral}
                pdf_data = create_pdf_report(nome_cliente, periodo_relatorio, totais_pdf, df_cheio, df_proporcional)
                faturamento_data_log = {
                    "cliente": nome_cliente, "periodo_relatorio": periodo_relatorio,
                    "valor_total": faturamento_total_geral, "terminais_cheio": len(df_cheio),
                    "terminais_proporcional": len(df_proporcional), "terminais_gprs": total_gprs,
                    "terminais_satelitais": total_satelital
                }

                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    st.download_button(
                       label="📥 Exportar Excel e Salvar Histórico",
                       data=excel_data,
                       file_name=f"Faturamento_{nome_cliente.replace(' ', '_')}_{datetime.now().strftime('%Y-%m')}.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                       on_click=umdb.log_faturamento, args=(faturamento_data_log,)
                    )
                with col_btn2:
                    st.download_button(
                       label="📄 Exportar Resumo em PDF",
                       data=pdf_data,
                       file_name=f"Resumo_Faturamento_{nome_cliente.replace(' ', '_')}_{datetime.now().strftime('%Y-%m')}.pdf",
                       mime="application/pdf"
                    )

                st.markdown("---")

                with st.expander("Detalhamento do Faturamento Proporcional"):
                    if not df_proporcional.empty:
                        st.dataframe(
                            df_proporcional[['Terminal', 'Nº Equipamento', 'Placa', 'Tipo', 'Data Desativação', 'Dias Ativos Mês', 'Suspenso Dias Mes', 'Dias a Faturar', 'Valor Unitario', 'Valor a Faturar']],
                            use_container_width=True, hide_index=True,
                            column_config={
                                "Data Desativação": st.column_config.DatetimeColumn("Data Desativação", format="DD/MM/YYYY"),
                                "Valor Unitario": st.column_config.NumberColumn("Valor Mensal Cheio (R$)", format="R$ %.2f"),
                                "Valor a Faturar": st.column_config.NumberColumn("Valor a Faturar (R$)", format="R$ %.2f")
                            }
                        )
                    else:
                        st.info("Nenhum terminal com faturamento proporcional neste período.")
                
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
