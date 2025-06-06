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

# 2. BLOCO DE VERIFICAÇÃO DE AUTENTICAÇÃO (CORRIGIDO)
# Este bloco agora busca o usuário real do st.session_state
auth_status = st.session_state.get("authentication_status", False)
if auth_status is not True:
    st.error("🔒 Acesso Negado! Por favor, faça login na página principal para continuar.")
    print(f"ACCESS_DENIED_LOG (Simulador_Licitação.py): User not authenticated. Status: {auth_status}")
    try:
        # Garante que o usuário seja redirecionado para a página de login correta
        st.page_link("Simulador_Comercial.py", label="Ir para Login", icon="🏠")
    except Exception:
        st.info("Retorne à página principal para efetuar o login.")
    st.stop()

# Se chegou aqui, o usuário está autenticado.
# Buscando os dados do usuário do session_state
current_username = st.session_state.get('username', 'N/A')
current_role = st.session_state.get('role', 'Indefinido')
current_name = st.session_state.get('name', 'N/A')

# Log para verificar se os dados foram pegos corretamente
print(f"INFO_LOG (Simulador_Licitação.py): User '{current_username}' authenticated. Name: '{current_name}', Role: '{current_role}'")


# 3. Restante do código da sua página
try:
    st.image("imgs/logo.png", width=250) # Verifique o caminho
except Exception as e:
    st.info("Logo não encontrado.")


st.markdown("<h1 style='text-align: center; color: #54A033;'>Simulador para Licitações e Editais</h1>", unsafe_allow_html=True)
st.markdown("---")

# Exibe os dados do usuário que fez o login
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

st.sidebar.header("🔧 Custos de Serviços")
valor_instalacao = Decimal(str(st.sidebar.number_input("Custo Instalação (unitário)", min_value=0.0, value=50.0, step=10.0, format="%.2f", key="lic_valor_instalacao")))
valor_manutencao = Decimal(str(st.sidebar.number_input("Custo Manutenção (unitário)", min_value=0.0, value=50.0, step=10.0, format="%.2f", key="lic_valor_manutencao")))
valor_desinstalacao = Decimal(str(st.sidebar.number_input("Custo Desinstalação (unitário)", min_value=0.0, value=50.0, step=10.0, format="%.2f", key="lic_valor_desinstalacao")))


# 🔽 Seleção de itens e serviços
col1, col2 = st.columns(2)

with col1:
    st.markdown("### 📦 Selecione os Itens de Locação")
    itens_selecionados = []
    for item, preco in precoCusto.items():
        item_key = f"toggle_item_lic_{item.replace(' ', '_').replace('/', '_')}"
        if st.toggle(f"{item} - R$ {preco:,.2f}", key=item_key):
            itens_selecionados.append(item)

with col2:
    st.markdown("### 🛠️ Selecione os Serviços Adicionais")
    incluir_instalacao = st.toggle(f"Incluir Instalação", key="lic_toggle_instalacao")
    
    incluir_manutencao = st.toggle(f"Incluir Manutenção", key="lic_toggle_manutencao")
    if incluir_manutencao:
        qtd_manutencao = Decimal(st.number_input("Quantidade de Manutenções", min_value=1, value=1, step=1, key="lic_qtd_manutencao"))
    else:
        qtd_manutencao = Decimal("0")

    incluir_desinstalacao = st.toggle(f"Incluir Desinstalação", key="lic_toggle_desinstalacao")
    if incluir_desinstalacao:
        qtd_desinstalacao = Decimal(st.number_input("Quantidade de Desinstalações", min_value=1, value=1, step=1, key="lic_qtd_desinstalacao"))
    else:
        qtd_desinstalacao = Decimal("0")

st.markdown("---")

# 📌 Lógica de cálculo e exibição de resultados
if itens_selecionados or incluir_instalacao or incluir_manutencao or incluir_desinstalacao:
    
    detalhamento_proposta = []
    valor_total_locacao = Decimal("0")
    mensalidade_venda_unitaria = Decimal("0")

    # 1. Cálculo da Locação
    if itens_selecionados:
        valor_total_unitario_hw = sum(precoCusto[item] for item in itens_selecionados)
        mensalidade_custo_unitario = (valor_total_unitario_hw / Decimal(12)).quantize(Decimal('0.01'), rounding=ROUND_DOWN)
        mensalidade_venda_unitaria = (mensalidade_custo_unitario * (Decimal(1) + margem)).quantize(Decimal('0.01'), rounding=ROUND_DOWN)
        valor_total_locacao = (mensalidade_venda_unitaria * qtd * contrato).quantize(Decimal('0.01'), rounding=ROUND_DOWN)
        
        detalhamento_proposta.append({
            "SERVIÇO/PRODUTO": f"Locação de Equipamentos ({', '.join(itens_selecionados)})",
            "QUANTIDADE": f"{int(qtd)} unid. x {int(contrato)} meses",
            "VALOR UNITÁRIO": mensalidade_venda_unitaria,
            "VALOR TOTAL": valor_total_locacao
        })

    # 2. Cálculo dos Serviços Adicionais
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

    if incluir_manutencao and qtd_manutencao > 0:
        total_servico = (valor_manutencao * qtd_manutencao).quantize(Decimal('0.01'), rounding=ROUND_DOWN)
        valor_total_servicos += total_servico
        detalhamento_proposta.append({
            "SERVIÇO/PRODUTO": "Taxa de Manutenção",
            "QUANTIDADE": int(qtd_manutencao),
            "VALOR UNITÁRIO": valor_manutencao,
            "VALOR TOTAL": total_servico
        })

    if incluir_desinstalacao and qtd_desinstalacao > 0:
        total_servico = (valor_desinstalacao * qtd_desinstalacao).quantize(Decimal('0.01'), rounding=ROUND_DOWN)
        valor_total_servicos += total_servico
        detalhamento_proposta.append({
            "SERVIÇO/PRODUTO": "Taxa de Desinstalação",
            "QUANTIDADE": int(qtd_desinstalacao),
            "VALOR UNITÁRIO": valor_desinstalacao,
            "VALOR TOTAL": total_servico
        })

    # 3. Cálculo do Valor Global
    valor_total_contrato_global = valor_total_locacao + valor_total_servicos

    # 🔹 Exibição dos resultados
    st.success("✅ Cálculo da Proposta para Licitação realizado!")
    
    col_metric1, col_metric2 = st.columns(2)
    with col_metric1:
      if mensalidade_venda_unitaria > 0:
        st.metric(label="Mensalidade por Veículo (Locação)", value=f"R$ {mensalidade_venda_unitaria:,.2f}")
    
    with col_metric2:
      st.metric(label="💰 Valor Total Estimado do Contrato", value=f"R$ {valor_total_contrato_global:,.2f}")
    
    st.caption(f"Cálculo considerando {int(qtd)} veículo(s) em locação por {int(contrato)} meses, com margem de {margem*100:.0f}% sobre equipamentos.")

    # 🔹 Tabela de Detalhamento
    if detalhamento_proposta:
        st.markdown("### 📊 Detalhamento da Proposta")
        df = pd.DataFrame(detalhamento_proposta)
        
        total_row = pd.DataFrame([{
            "SERVIÇO/PRODUTO": "VALOR TOTAL GERAL", "QUANTIDADE": "", "VALOR UNITÁRIO": None, "VALOR TOTAL": valor_total_contrato_global
        }])
        df_final = pd.concat([df, total_row], ignore_index=True)

        st.dataframe(
            df_final,
            use_container_width=True,
            hide_index=True,
            column_config={
                "SERVIÇO/PRODUTO": st.column_config.TextColumn("Serviço/Produto"),
                "QUANTIDADE": st.column_config.TextColumn("Quantidade"),
                "VALOR UNITÁRIO": st.column_config.NumberColumn(
                    "Valor Unitário (R$)",
                    format="R$ %.2f"
                ),
                "VALOR TOTAL": st.column_config.NumberColumn(
                    "Valor Total (R$)",
                    format="R$ %.2f"
                ),
            }
        )

else:
    st.warning("⚠️ Selecione pelo menos um item ou serviço para calcular a proposta.")

st.markdown("---")
if st.button("🔄 Limpar Campos e Recalcular", key="lic_btn_limpar_recalcular"):
    st.rerun()
