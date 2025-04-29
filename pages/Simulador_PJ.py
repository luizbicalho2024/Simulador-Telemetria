import streamlit as st
from datetime import datetime
import base64
from jinja2 import Template
import os
import tempfile
import webbrowser

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

# Função para gerar a proposta HTML com design personalizado
def gerar_proposta_html(razao_social, responsavel, responsavel_comercial, data_proposta, 
                        produtos, qtd_veiculos, temp, valor_unitario, contrato_total):
    # Template HTML com design personalizado
    template_str = """
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Proposta Comercial - {{ razao_social }}</title>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap');
            
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
                font-family: 'Roboto', Arial, sans-serif;
            }
            
            body {
                background-color: #f9f9f9;
                color: #333;
                line-height: 1.6;
            }
            
            .container {
                max-width: 1000px;
                margin: 20px auto;
                background: white;
                padding: 40px;
                box-shadow: 0 0 20px rgba(0,0,0,0.1);
                position: relative;
            }
            
            .header {
                display: flex;
                align-items: center;
                justify-content: space-between;
                margin-bottom: 30px;
                border-bottom: 2px solid #54A033;
                padding-bottom: 20px;
            }
            
            .logo img {
                max-width: 200px;
            }
            
            .title {
                text-align: center;
                flex-grow: 1;
            }
            
            .title h1 {
                color: #54A033;
                font-size: 28px;
                font-weight: 700;
                margin-bottom: 5px;
            }
            
            .title p {
                color: #666;
                font-size: 16px;
            }
            
            .client-info {
                background: #f5f5f5;
                padding: 20px;
                margin-bottom: 30px;
                border-radius: 5px;
                border-left: 5px solid #54A033;
            }
            
            .client-info table {
                width: 100%;
                border-collapse: collapse;
            }
            
            .client-info td {
                padding: 10px;
                vertical-align: top;
            }
            
            .client-info .label {
                font-weight: 700;
                width: 35%;
                color: #444;
            }
            
            .section-title {
                color: #54A033;
                margin: 30px 0 15px;
                padding-bottom: 10px;
                border-bottom: 1px solid #ddd;
                font-size: 22px;
                font-weight: 500;
            }
            
            .proposta-info {
                margin-bottom: 30px;
            }
            
            .produtos-table {
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0 30px;
                box-shadow: 0 0 10px rgba(0,0,0,0.05);
            }
            
            .produtos-table th, .produtos-table td {
                padding: 12px 15px;
                text-align: left;
                border-bottom: 1px solid #ddd;
            }
            
            .produtos-table th {
                background-color: #54A033;
                color: white;
                font-weight: 500;
            }
            
            .produtos-table tr:nth-child(even) {
                background-color: #f9f9f9;
            }
            
            .produtos-table tr:hover {
                background-color: #f1f1f1;
            }
            
            .total-row {
                font-weight: 700;
                background-color: #eafcef !important;
            }
            
            .summary {
                background: #f5f5f5;
                padding: 20px;
                margin: 30px 0;
                border-radius: 5px;
                border-left: 5px solid #54A033;
            }
            
            .summary p {
                margin-bottom: 10px;
                font-size: 16px;
            }
            
            .summary .highlight {
                color: #54A033;
                font-weight: 700;
                font-size: 18px;
            }
            
            .terms {
                margin: 30px 0;
                font-size: 14px;
                color: #666;
            }
            
            .footer {
                margin-top: 50px;
                text-align: center;
                color: #666;
                font-size: 14px;
                border-top: 1px solid #ddd;
                padding-top: 20px;
            }
            
            .signatures {
                display: flex;
                justify-content: space-between;
                margin-top: 100px;
            }
            
            .signature {
                width: 45%;
                text-align: center;
            }
            
            .signature hr {
                border: none;
                border-top: 1px solid #000;
                margin-bottom: 5px;
            }
            
            .signature p {
                font-size: 14px;
            }
            
            @media print {
                body {
                    background: white;
                }
                
                .container {
                    box-shadow: none;
                    margin: 0;
                    padding: 20px;
                    max-width: 100%;
                }
                
                .print-button {
                    display: none;
                }
            }
            
            .print-button {
                position: absolute;
                top: 20px;
                right: 20px;
                background: #54A033;
                color: white;
                border: none;
                padding: 10px 15px;
                border-radius: 4px;
                cursor: pointer;
                font-weight: 500;
                transition: background 0.3s;
            }
            
            .print-button:hover {
                background: #458729;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <button class="print-button" onclick="window.print()">Imprimir Proposta</button>
            
            <div class="header">
                <div class="logo">
                    <img src="data:image/png;base64,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" alt="Logo da Empresa">
                </div>
                <div class="title">
                    <h1>PROPOSTA COMERCIAL E INTENÇÃO DE COMPRA</h1>
                    <p>Soluções avançadas de monitoramento veicular</p>
                </div>
            </div>
            
            <div class="client-info">
                <table>
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
            </div>
            
            <div class="proposta-info">
                <h2 class="section-title">1. INTRODUÇÃO</h2>
                <p>Agradecemos a oportunidade de apresentar nossa proposta comercial. Nossa empresa é especializada em soluções de rastreamento e monitoramento veicular, proporcionando mais segurança e eficiência para sua frota.</p>
                
                <h2 class="section-title">2. SOBRE NÓS</h2>
                <p>Somos uma empresa líder no mercado de tecnologia para gestão de frotas, oferecendo soluções inovadoras que atendem às necessidades específicas de cada cliente. Nossa infraestrutura tecnológica e equipe altamente capacitada garantem um serviço de excelência.</p>
                
                <h2 class="section-title">3. NOSSOS SERVIÇOS</h2>
                <p>Oferecemos uma ampla gama de serviços de monitoramento e rastreamento veicular, desde soluções básicas até avançados sistemas de videomonitoramento com inteligência artificial para prevenção de acidentes e monitoramento de motoristas.</p>
                
                <h2 class="section-title">4. BENEFÍCIOS</h2>
                <ul>
                    <li>Redução de custos operacionais</li>
                    <li>Aumento da segurança da frota</li>
                    <li>Otimização de rotas e redução do consumo de combustível</li>
                    <li>Monitoramento em tempo real</li>
                    <li>Relatórios detalhados de operação</li>
                    <li>Suporte técnico especializado 24/7</li>
                </ul>
                
                <h2 class="section-title">5. PLANO E VALORES</h2>
                <table class="produtos-table">
                    <thead>
                        <tr>
                            <th>#</th>
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
                        <tr class="total-row">
                            <td colspan="2">Valor Total por Veículo:</td>
                            <td>{{ "%.2f"|format(soma_total) }}</td>
                        </tr>
                    </tbody>
                </table>
            </div>
            
            <div class="summary">
                <p><strong>Quantidade de Veículos:</strong> {{ qtd_veiculos }}</p>
                <p><strong>Tempo de Contrato:</strong> {{ temp }}</p>
                <p><strong>Valor Mensal:</strong> R$ {{ "%.2f"|format(valor_unitario) }}</p>
                <p class="highlight"><strong>Valor Total do Contrato:</strong> R$ {{ "%.2f"|format(contrato_total) }}</p>
            </div>
            
            <div class="terms">
                <h2 class="section-title">6. CONDIÇÕES COMERCIAIS</h2>
                <p><strong>Forma de Pagamento:</strong> Mensal</p>
                <p><strong>Prazo de Instalação:</strong> Até 15 dias úteis após assinatura do contrato</p>
                <p><strong>Validade da Proposta:</strong> 30 dias a partir da data de emissão</p>
                <p><strong>Suporte Técnico:</strong> 24 horas por dia, 7 dias por semana</p>
                <p><strong>Garantia:</strong> Durante toda a vigência do contrato</p>
            </div>
            
            <div class="terms">
                <h2 class="section-title">7. TERMOS E CONDIÇÕES</h2>
                <p>Esta proposta está sujeita aos termos e condições gerais de serviço, que serão detalhados no contrato a ser assinado entre as partes.</p>
                <p>A instalação dos equipamentos será realizada por técnicos credenciados e de acordo com o cronograma a ser definido em conjunto com o cliente.</p>
                <p>Todos os valores apresentados já incluem impostos e taxas aplicáveis.</p>
            </div>
            
            <div class="signatures">
                <div class="signature">
                    <hr>
                    <p>Assinatura do Cliente</p>
                    <p>{{ razao_social }}</p>
                </div>
                <div class="signature">
                    <hr>
                    <p>Assinatura do Representante</p>
                    <p>{{ responsavel_comercial }}</p>
                </div>
            </div>
            
            <div class="footer">
                <p>© 2025 - Todos os direitos reservados</p>
                <p>Esta proposta é confidencial e de uso exclusivo do destinatário.</p>
            </div>
        </div>
        
        <script>
            // Script para abrir automaticamente a janela de impressão quando solicitado
            function printDocument() {
                window.print();
            }
        </script>
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
        soma_total=soma_total,
        valor_unitario=valor_total,
        contrato_total=contrato_total
    )
    
    return html_content

# Modificando a função para abrir a proposta em uma nova guia
def abrir_proposta_em_nova_guia(html_content):
    # Cria um arquivo temporário
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.html')
    temp_file.write(html_content.encode())
    temp_file.close()
    
    # Constrói o URL do arquivo
    file_url = f'file://{temp_file.name}'
    
    # Abre em uma nova guia do navegador
    webbrowser.open_new_tab(file_url)
    
    return temp_file.name

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
        
        # Abrir a proposta em uma nova guia
        temp_path = abrir_proposta_em_nova_guia(html_content)
        
        st.success(f"✅ Proposta aberta em uma nova guia do navegador e pronta para impressão!")
        
        # Mostrar preview da proposta
        st.markdown("---")
        st.markdown("### 📝 Pré-visualização da Proposta")
        st.components.v1.html(html_content, height=600, scrolling=True)