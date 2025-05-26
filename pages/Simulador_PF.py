# pages/Simulador_PF.py
from decimal import Decimal, ROUND_DOWN # Importações Python padrão primeiro
import streamlit as st

# 1. st.set_page_config() - PRIMEIRO COMANDO STREAMLIT
st.set_page_config(
    layout="wide",
    page_title="Simulador Pessoa Física", # Título da aba específico
    page_icon="imgs/v-c.png", # Verifique se o caminho para a imagem do ícone está correto
    initial_sidebar_state="expanded"
)

# 2. BLOCO DE VERIFICAÇÃO DE AUTENTICAÇÃO
auth_status = st.session_state.get("authentication_status", False)
if auth_status is not True:
    st.error("🔒 Acesso Negado! Por favor, faça login na página principal para continuar.")
    print(f"ACCESS_DENIED_LOG (Simulador_PF.py): User not authenticated. Status: {auth_status}")
    try:
        # Certifique-se que o nome do arquivo da página principal está correto aqui
        st.page_link("Simulador_Comercial.py", label="Ir para Login", icon="🏠")
    except AttributeError: 
        st.info("Retorne à página principal para efetuar o login.")
    st.stop() 

# Se chegou aqui, o usuário está autenticado.
current_username = st.session_state.get('username', 'N/A')
current_role = st.session_state.get('role', 'Indefinido') # Será 'Indefinido' se não for pego corretamente no login
current_name = st.session_state.get('name', 'N/A')

print(f"INFO_LOG (Simulador_PF.py): User '{current_username}' authenticated. Role: '{current_role}'")

# 3. Restante do código da sua página - AGORA o conteúdo da página começa
# 🔵 Logotipo e cabeçalho estilizado
try:
    st.image("imgs/logo.png", width=250) # Verifique o caminho
except FileNotFoundError:
    print("WARN_LOG (Simulador_PF.py): Arquivo imgs/logo.png não encontrado.")
    # st.warning("Logo não encontrado.") # Opcional: mostrar aviso na UI
except Exception as e_img:
    print(f"WARN_LOG (Simulador_PF.py): Erro ao carregar imgs/logo.png: {e_img}")

st.markdown("<h1 style='text-align: center; color: #54A033;'>Simulador de Venda - Pessoa Física</h1>", unsafe_allow_html=True)
st.markdown("---")

# Informações do usuário logado (após o cabeçalho principal da página)
st.write(f"Usuário: {current_name} ({current_username})")
st.write(f"Nível de Acesso: {current_role}")
st.markdown("---")

# Exemplo de verificação de papel (role) se necessário dentro desta página específica:
# if current_role == "admin":
#     st.write("Conteúdo específico para Admin nesta página de PF.")
# elif current_role == "user":
#     st.write("Conteúdo específico para Usuário Comum nesta página de PF.")
# else: # Se current_role for 'Indefinido' ou outro valor inesperado
#     st.warning("Papel do usuário não definido, funcionalidades podem ser limitadas.")


# 📌 Definição dos preços (usando Decimal para precisão)
precos = {
    "GPRS / Gsm": Decimal("970.56"), # Use strings para Decimal para evitar problemas de float
    "Satelital": Decimal("2325.60")
}

# 🎯 Seção de entrada de dados na Sidebar
st.sidebar.header("📝 Configurações PF") # Título mais específico para esta página
# Chaves únicas para widgets da sidebar
modeloPF_key = "pf_modelo_rastreador_sb"
modeloPF = st.sidebar.selectbox("Tipo de Rastreador 📡", list(precos.keys()), key=modeloPF_key)

# 🔢 Exibir preço à vista
preco_base = precos[modeloPF] # preco_base será Decimal
st.markdown(f"### 💰 Valor Anual À Vista: R$ {preco_base:,.2f}")

# 🔽 Opção de desconto
st.markdown("### 🎯 Aplicar Desconto:")
col1_desc, col2_desc = st.columns([1, 3]) # Renomeadas para evitar conflito com outras colunas
# Chaves únicas
desconto_checkbox_key = "pf_desconto_checkbox"
desconto_percent_key = "pf_desconto_percent_input"

with col1_desc: # Usando a variável renomeada
    desconto_ativo = st.checkbox("Ativar Desconto", value=False, key=desconto_checkbox_key)

desconto_calculado = preco_base # Valor padrão é o preço base

if desconto_ativo:
    with col2_desc: # Usando a variável renomeada
        porcentagem_desconto = Decimal(str(st.number_input("Percentual de Desconto (%)", min_value=0.0, max_value=100.0, value=0.0, step=1.0, key=desconto_percent_key, format="%.2f")))
    
    if porcentagem_desconto > Decimal("0"):
        valor_do_desconto = (preco_base * (porcentagem_desconto / Decimal("100"))).quantize(Decimal('0.01'), rounding=ROUND_DOWN)
        desconto_calculado = (preco_base - valor_do_desconto).quantize(Decimal('0.01'), rounding=ROUND_DOWN)
        st.success(f"✅ {porcentagem_desconto}% de desconto aplicado!")
        st.info(f"💰 **Valor com Desconto:** R$ {desconto_calculado:,.2f}")
    else:
        # Se o desconto estiver ativo mas a porcentagem for 0, não mostra mensagem de sucesso
        # desconto_calculado já é preco_base
        pass 
else:
    # desconto_calculado já é preco_base
    pass


# 🔽 Opção de parcelamento
st.markdown("### 💳 Parcelamento:")
# Chaves únicas
parcelamento_checkbox_key = "pf_parcelamento_checkbox"
parcelamento_num_parcelas_key = "pf_parcelamento_num_parcelas_sb"

parcelamento_ativo = st.checkbox("Ativar Parcelamento", value=False, key=parcelamento_checkbox_key)

if parcelamento_ativo:
    num_parcelas = st.selectbox("Quantidade de Parcelas:", options=[i for i in range(2, 13)], key=parcelamento_num_parcelas_key)
    
    # A lógica da margem precisa ser revista para ser aplicada corretamente ao valor já com desconto
    # Margem de 4.08% AO MÊS é muito alta. Se for uma taxa de juros da máquina de cartão,
    # ela geralmente é aplicada sobre o valor da venda.
    # Exemplo: se a taxa da máquina é 4.08% para 'num_parcelas', não se multiplica pelo número de parcelas assim.
    # A lógica de juros de parcelamento é mais complexa.
    # Simplificando para uma taxa fixa sobre o valor a ser parcelado (desconto_calculado)
    # Esta é uma INTERPRETAÇÃO da sua lógica original, que pode precisar de ajuste financeiro real.
    
    # Se a margem é uma taxa de juros composta simples para o período:
    # margem_parcelamento_percentual = Decimal(str(num_parcelas)) * Decimal("0.0408") # Sua lógica original, resulta em juros muito altos
    # Para uma taxa de juros de exemplo de 2% a.m. (Price), o cálculo seria diferente.
    # Assumindo que 4.08% é um fator fixo de acréscimo por parcela (simplificação)
    
    # Vamos manter sua lógica original de margem por enquanto, mas com Decimal:
    margem_fator = Decimal(str(num_parcelas)) * Decimal("0.0408") 
    
    # O valor a ser parcelado é o 'desconto_calculado'
    valor_a_parcelar_com_juros = desconto_calculado * (Decimal(1) + margem_fator)
    valor_parcela = (valor_a_parcelar_com_juros / Decimal(str(num_parcelas))).quantize(Decimal('0.01'), rounding=ROUND_DOWN)
    total_parcelado = (valor_parcela * Decimal(str(num_parcelas))).quantize(Decimal('0.01'), rounding=ROUND_DOWN)

    st.success(f"✅ Parcelado em {num_parcelas}x")
    st.info(f"📄 **{num_parcelas} Parcelas de:** R$ {valor_parcela:,.2f}")
    st.markdown(f"### 💰 Valor Total Parcelado: R$ {total_parcelado:,.2f}")
    st.caption(f"(Juros/taxas de parcelamento já incluídos no valor da parcela e no total)")

# 🎯 Botão para limpar/reiniciar
if st.button("🔄 Limpar Campos PF", key="pf_btn_limpar_v2"): # Chave única
    # A forma mais simples de limpar todos os inputs para seus valores default é o rerun
    # Para um reset mais granular, você teria que gerenciar cada input no st.session_state
    st.rerun()