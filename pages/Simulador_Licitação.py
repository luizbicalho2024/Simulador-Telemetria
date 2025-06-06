# pages/Simulador_Licitação.py
from decimal import Decimal, ROUND_DOWN # Importações Python primeiro
import pandas as pd # Importado para criar a tabela de detalhamento
import streamlit as st

# 1. st.set_page_config() - PRIMEIRO COMANDO STREAMLIT
st.set_page_config(
    layout="wide",
    page_title="Simulador Licitações e Editais", # Título da aba específico
    page_icon="imgs/v-c.png", # Verifique se o caminho está correto
    initial_sidebar_state="expanded"
)

# 2. BLOCO DE VERIFICAÇÃO DE AUTENTICAÇÃO
# auth_status = st.session_state.get("authentication_status", False)
# if auth_status is not True:
#     st.error("🔒 Acesso Negado! Por favor, faça login na página principal para continuar.")
#     print(f"ACCESS_DENIED_LOG (Simulador_Licitação.py): User not authenticated. Status: {auth_status}")
#     try:
#         st.page_link("Simulador_Comercial.py", label="Ir para Login", icon="🏠")
#     except AttributeError:
#         st.info("Retorne à página principal para efetuar o login.")
#     st.stop()

# # Se chegou aqui, o usuário está autenticado.
# current_username = st.session_state.get('username', 'N/A')
# current_role = st.session_state.get('role', 'Indefinido') # Será 'Indefinido' se não for pego corretamente no login
# current_name = st.session_state.get('name', 'N/A')

# print(f"INFO_LOG (Simulador_Licitação.py): User '{current_username}' authenticated. Role: '{current_role}'")

# --- Bloco de Autenticação Mock (para teste) ---
# Remova ou comente este bloco e descomente o bloco acima quando em produção
current_name = "Usuário Teste"
current_username = "teste"
current_role = "Admin"
# --- Fim do Bloco Mock ---


# 3. Restante do código da sua página
try:
    st.image("imgs/logo.png", width=250) # Verifique o caminho
except Exception as e:
    st.info("Logo não encontrado. Usando placeholder.")


st.markdown("<h1 style='text-align: center; color: #54A033;'>Simulador para Licitações e Editais</h1>", unsafe_allow_html=True)
st.markdown("---")

st.write(f"Usuário: {current_name} ({current_username})")
st.write(f"Nível de Acesso: {current_role}")
st.markdown("---")

# 📌 Tabela de preços de equipamentos convertida para Decimal
precoCusto = {
    "Rastreador GPRS/GSM 2G": Decimal("300"),
    "Rastreador GPRS/GSM 4G": Decimal("400"),
    "Rastreador Satelital": Decimal("900"),
    "Telemetria/CAN": Decimal("600"),
    "RFID - ID Motorista": Decimal("153"),
}

# 🎯 Sidebar para entrada de dados
st.sidebar.header("📝 Configurações da Licitação")
qtd = Decimal(st.sidebar.number_input("Quantidade de Veículos 🚗", min_value=1, value=1, step=1, key="lic_qtd_veiculos"))
contrato = Decimal(st.sidebar.number_input("Tempo de Contrato (meses) 📆", min_value=1, value=12, step=1, key="lic_tempo_contrato"))
margem = Decimal(str(st.sidebar.slider("Margem de Lucro (%) 📈", min_value=0.0, max_value=1.0, value=0.3, step=0.01, format="%.2f", key="lic_margem_lucro")))

# NOVOS INPUTS PARA SERVIÇOS ADICIONAIS NA SIDEBAR
st.sidebar.header("🔧 Serviços Adicionais")
valor_instalacao = Decimal(str(st.sidebar.number_input("Valor Instalação (unitário)", min_value=0.0, value=50.0, step=10.0, format="%.2f", key="lic_valor_instalacao")))
valor_manutencao = Decimal(str(st.sidebar.number_input("Valor Manutenção (unitário)", min_value=0.0, value=50.0, step=10.0, format="%.2f", key="lic_valor_manutencao")))
valor_desinstalacao = Decimal(str(st.sidebar.number_input("Valor Desinstalação (unitário)", min_value=0.0, value=50.0, step=10.0, format="%.2f", key="lic_valor_desinstalacao")))


# 🔽 Seleção de itens e serviços
col1, col2 = st.columns(2)

with col1:
    st.markdown("### 📦 Selecione os Itens")
    itens_selecionados = []
    # Usar um loop para criar os toggles de itens
    for item, preco in precoCusto.items():
        item_key = f"toggle_item_lic_{item.replace(' ', '_').replace('/', '_')}"
        if st.toggle(f"{item} - R$ {preco:,.2f}", key=item_key):
            itens_selecionados.append(item)

with col2:
    st.markdown("### 🛠️ Selecione os Serviços")
    # Toggles para incluir os serviços adicionais no cálculo
    incluir_instalacao = st.toggle(f"Incluir Instalação (R$ {valor_instalacao:,.2f})", key="lic_toggle_instalacao")
    incluir_manutencao = st.toggle(f"Incluir Manutenção (R$ {valor_manutencao:,.2f})", key="lic_toggle_manutencao")
    incluir_desinstalacao = st.toggle(f"Incluir Desinstalação (R$ {valor_desinstalacao:,.2f})", key="lic_toggle_desinstalacao")


st.markdown("---")

# 📌 Lógica de cálculo e exibição de resultados
# A condição agora verifica se há itens ou serviços selecionados
if itens_selecionados or incluir_instalacao or incluir_manutencao or incluir_desinstalacao:
    
    detalhamento_proposta = []
    valor_total_locacao = Decimal("0")
    mensalidade_venda_unitaria = Decimal("0")

    # 1. Cálculo da Locação (se houver itens)
    if itens_selecionados:
        valor_total_unitario_hw = sum(precoCusto[item] for item in itens_selecionados)
        mensalidade_custo_unitario = (valor_total_unitario_hw / Decimal(12)).quantize(Decimal('0.01'), rounding=ROUND_DOWN)
        mensalidade_venda_unitaria = (mensalidade_custo_unitario * (Decimal(1) + margem)).quantize(Decimal('0.01'), rounding=ROUND_DOWN)
        valor_total_locacao = (mensalidade_venda_unitaria * qtd * contrato).quantize(Decimal('0.01'), rounding=ROUND_DOWN)
        
        # Adiciona à lista para a tabela
        detalhamento_proposta.append({
            "SERVIÇO/PRODUTO": f"Locação de Equipamentos ({', '.join(itens_selecionados)})",
            "QUANTIDADE": f"{int(qtd)} x {int(contrato)} meses",
            "VALOR UNITÁRIO": mensalidade_venda_unitaria,
            "VALOR TOTAL": valor_total_locacao
        })

    # 2. Cálculo dos Serviços Adicionais (custos únicos)
    valor_total_servicos = Decimal("0")

    if incluir_instalacao:
        total_servico = (valor_instalacao * qtd).quantize(Decimal('0.01'), rounding=ROUND_DOWN)
        valor_total_servicos += total_servico
        detalhamento_proposta.append({
            "SERVIÇO/PRODUTO": "Taxa de Instalação",
            "QUANTIDADE": int(qtd),
            "VALOR UNITÁRIO": valor_instalacao,
            "VALOR TOTAL": total_servico
        })

    if incluir_manutencao:
        total_servico = (valor_manutencao * qtd).quantize(Decimal('0.01'), rounding=ROUND_DOWN)
        valor_total_servicos += total_servico
        detalhamento_proposta.append({
            "SERVIÇO/PRODUTO": "Taxa de Manutenção",
            "QUANTIDADE": int(qtd),
            "VALOR UNITÁRIO": valor_manutencao,
            "VALOR TOTAL": total_servico
        })

    if incluir_desinstalacao:
        total_servico = (valor_desinstalacao * qtd).quantize(Decimal('0.01'), rounding=ROUND_DOWN)
        valor_total_servicos += total_servico
        detalhamento_proposta.append({
            "SERVIÇO/PRODUTO": "Taxa de Desinstalação",
            "QUANTIDADE": int(qtd),
            "VALOR UNITÁRIO": valor_desinstalacao,
            "VALOR TOTAL": total_servico
        })

    # 3. Cálculo do Valor Global do Contrato
    valor_total_contrato_global = valor_total_locacao + valor_total_servicos

    # 🔹 Exibição dos resultados principais
    st.success("✅ Cálculo da Proposta para Licitação realizado!")
    
    col_metric1, col_metric2 = st.columns(2)
    with col_metric1:
      # Exibe a mensalidade apenas se houver equipamentos selecionados
      if mensalidade_venda_unitaria > 0:
        st.metric(label="Mensalidade por Veículo (Locação)", value=f"R$ {mensalidade_venda_unitaria:,.2f}")
    
    with col_metric2:
      st.metric(label="💰 Valor Total Estimado do Contrato", value=f"R$ {valor_total_contrato_global:,.2f}")
    
    st.caption(f"Cálculo considerando {int(qtd)} veículo(s) por {int(contrato)} meses, com margem de {margem*100:.0f}% sobre equipamentos.")

    # 🔹 EXIBIÇÃO DA TABELA DE DETALHAMENTO
    if detalhamento_proposta:
        st.markdown("### 📊 Detalhamento da Proposta")
        df = pd.DataFrame(detalhamento_proposta)

        # Adicionar linha de total
        total_row = pd.DataFrame([{
            "SERVIÇO/PRODUTO": "VALOR TOTAL GERAL",
            "QUANTIDADE": "",
            "VALOR UNITÁRIO": "",
            "VALOR TOTAL": valor_total_contrato_global
        }])
        
        df_final = pd.concat([df, total_row], ignore_index=True)

        # Exibindo o DataFrame com formatação
        st.dataframe(
            df_final,
            use_container_width=True,
            column_config={
                "VALOR UNITÁRIO": st.column_config.NumberColumn(
                    "Valor Unitário (R$)",
                    format="%.2f",
                ),
                "VALOR TOTAL": st.column_config.NumberColumn(
                    "Valor Total (R$)",
                    format="%.2f",
                ),
            },
            hide_index=True,
        )

else:
    st.warning("⚠️ Selecione pelo menos um item ou serviço para calcular a proposta.")

st.markdown("---")
# 🎯 Botão para limpar seleção (reinicia a página)
if st.button("🔄 Limpar Campos e Recalcular", key="lic_btn_limpar_recalcular"):
    st.rerun()

