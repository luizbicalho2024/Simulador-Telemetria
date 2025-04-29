import streamlit as st
from datetime import datetime
import base64
from jinja2 import Template

# 🛠️ Configuração da página
st.set_page_config(
    layout="wide", 
    page_title="Simulador PJ", 
    page_icon="imgs/v-c.png", 
    initial_sidebar_state="expanded"
)

# 🔵 Logotipo e cabeçalho estilizado
st.image("imgs/logo.png", width=250)
st.markdown("<h1 style='text-align: center; color: #54A033;'>Simulador de Venda - Pessoa Jurídica</h1>", unsafe_allow_html=True)
st.markdown("---")

# 📌 Definição dos preços para cada plano
planos = {
    "12 Meses": {
        "GPRS / Gsm": 80.88,
        "Satélite": 193.80,
        "Identificador de Motorista / RFID": 19.25,
        "Leitor de Rede CAN / Telemetria": 75.25,
        "Videomonitoramento + DMS + ADAS": 409.11
    },
    "24 Meses": {
        "GPRS / Gsm": 53.92,
        "Satélite": 129.20,
        "Identificador de Motorista / RFID": 12.83,
        "Leitor de Rede CAN / Telemetria": 50.17,
        "Videomonitoramento + DMS + ADAS": 272.74
    },
    "36 Meses": {
        "GPRS / Gsm": 44.93,
        "Satélite": 107.67,
        "Identificador de Motorista / RFID": 10.69,
        "Leitor de Rede CAN / Telemetria": 41.81,
        "Videomonitoramento + DMS + ADAS": 227.28
    }
}

# 📊 Seção de entrada de dados
st.sidebar.header("📝 Configurações")
razao_social = st.sidebar.text_input("Razão Social 🏢")
responsavel = st.sidebar.text_input("Nome do Responsável 👤")
responsavel_comercial = st.sidebar.text_input("Responsável Comercial 🤝")
data_proposta = st.sidebar.date_input("Data da Proposta 📅", value=datetime.today())
qtd_veiculos = st.sidebar.number_input("Quantidade de Veículos 🚗", min_value=1, value=1, step=1)
temp = st.sidebar.selectbox("Tempo de Contrato ⏳", list(planos.keys()))

# 🔽 Exibir botões de produtos
st.markdown("### 🛠️ Selecione os Produtos:")
col1, col2 = st.columns(2)

selecionados = []
produtos_selecionados = []
valores = planos[temp]

for i, (produto, preco) in enumerate(valores.items()):
    col = col1 if i % 2 == 0 else col2
    toggle = col.toggle(f"{produto} - R$ {preco:,.2f}")
    if toggle:
        selecionados.append(preco)
        produtos_selecionados.append({
            "nome": produto,
            "valor_unitario": preco
        })

# 🔢 Cálculo dos valores
soma_total = sum(selecionados)
valor_total = soma_total * qtd_veiculos
contrato_total = valor_total * int(temp.split()[0])

# 🏆 Exibir os resultados
st.markdown("---")
st.markdown("### 💰 **Resumo da Cotação:**")
st.success(f"✅ **Valor Unitário:** R$ {valor_total:,.2f}")
st.info(f"📄 **Valor Total do Contrato ({temp}):** R$ {contrato_total:,.2f}")

# 🎯 Botão para limpar seleção
if st.button("🔄 Limpar Seleção"):
    st.rerun()

# Função para gerar a proposta HTML
def gerar_proposta_html(razao_social, responsavel, responsavel_comercial, data_proposta, produtos, qtd_veiculos, temp, valor_total, contrato_total):
    # Template HTML com Jinja2
    template_str = """
    <!DOCTYPE html>
    <html xmlns="http://www.w3.org/1999/xhtml">
    <head>
    <meta charset="utf-8"/>
    <meta name="generator" content="pdf2htmlEX"/>
    <meta http-equiv="X-UA-Compatible" content="IE=edge,chrome=1"/>
    <title>Proposta Comercial</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { text-align: center; margin-bottom: 30px; }
        .info-table { width: 100%; border-collapse: collapse; margin-bottom: 20px; }
        .info-table td { padding: 8px; border: 1px solid #ddd; }
        .info-table .label { font-weight: bold; width: 30%; }
        .produtos-table { width: 100%; border-collapse: collapse; margin-bottom: 20px; }
        .produtos-table th, .produtos-table td { padding: 10px; border: 1px solid #ddd; text-align: left; }
        .produtos-table th { background-color: #f2f2f2; }
        .total { font-weight: bold; text-align: right; }
        .footer { margin-top: 50px; text-align: center; font-size: 12px; }
        .signature { margin-top: 80px; border-top: 1px solid #000; width: 300px; text-align: center; padding-top: 5px; }
    </style>
    </head>
    <body>
        <div class="header">
            <h1>PROPOSTA COMERCIAL E INTENÇÃO DE COMPRA</h1>
        </div>
        
        <table class="info-table">
            <tr>
                <td class="label">Razão Social:</td>
                <td>{{ razao_social }}</td>
            </tr>
            <tr>
                <td class="label">Responsável:</td>
                <td>{{ responsavel }}</td>
            </tr>
            <tr>
                <td class="label">Responsável Comercial:</td>
                <td>{{ responsavel_comercial }}</td>
            </tr>
            <tr>
                <td class="label">Data da Proposta:</td>
                <td>{{ data_proposta }}</td>
            </tr>
        </table>
        
        <h3>5. PLANO E VALORES</h3>
        <table class="produtos-table">
            <thead>
                <tr>
                    <th>Item</th>
                    <th>Descrição</th>
                    <th>Valor Unitário (R$)</th>
                </tr>
            </thead>
            <tbody>
                {% for produto in produtos %}
                <tr>
                    <td>{{ loop.index }}</td>
                    <td>{{ produto.nome }}</td>
                    <td>{{ "%.2f"|format(produto.valor_unitario) }}</td>
                </tr>
                {% endfor %}
                <tr>
                    <td colspan="2" class="total">Valor Total por Veículo:</td>
                    <td>{{ "%.2f"|format(valor_total) }}</td>
                </tr>
            </tbody>
        </table>
        
        <p><strong>Quantidade de Veículos:</strong> {{ qtd_veiculos }}</p>
        <p><strong>Tempo de Contrato:</strong> {{ temp }}</p>
        <p><strong>Valor Total do Contrato:</strong> R$ {{ "%.2f"|format(contrato_total) }}</p>
        
        <div class="footer">
            <p>Proposta válida por 30 dias a partir da data de emissão.</p>
            <div class="signature">
                <p>_________________________________________</p>
                <p>Assinatura do Responsável</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    template = Template(template_str)
    html_content = template.render(
        razao_social=razao_social,
        responsavel=responsavel,
        responsavel_comercial=responsavel_comercial,
        data_proposta=data_proposta.strftime("%d/%m/%Y"),
        produtos=produtos_selecionados,
        qtd_veiculos=qtd_veiculos,
        temp=temp,
        valor_total=valor_total,
        contrato_total=contrato_total
    )
    
    return html_content

# Botão para gerar proposta
if st.button("📄 Gerar Proposta"):
    if not razao_social or not responsavel or not responsavel_comercial:
        st.error("Por favor, preencha todos os campos obrigatórios (Razão Social, Responsável e Responsável Comercial).")
    elif not produtos_selecionados:
        st.error("Por favor, selecione pelo menos um produto.")
    else:
        html_content = gerar_proposta_html(
            razao_social,
            responsavel,
            responsavel_comercial,
            data_proposta,
            produtos_selecionados,
            qtd_veiculos,
            temp,
            valor_total,
            contrato_total
        )
        
        # Criar link para download
        b64 = base64.b64encode(html_content.encode()).decode()
        href = f'data:text/html;base64,{b64}'
        st.markdown(f'<a href="{href}" download="proposta_comercial.html">⬇️ Baixar Proposta Comercial</a>', unsafe_allow_html=True)
        
        # Mostrar preview da proposta
        st.markdown("---")
        st.markdown("### 📝 Pré-visualização da Proposta")
        st.components.v1.html(html_content, height=1000, scrolling=True)