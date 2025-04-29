import requests
import streamlit as st

# URL do documento DOCX no Google Docs
docx_url = "https://docs.google.com/document/d/1GlfhBo6SfzJzcfV-TaxGCWoyrENJJo7g/export?format=docx"

# URL da API do ConvertAPI para conversão de DOCX para PDF
convertapi_url = "https://v2.convertapi.com/convert/docx/to/pdf?Secret=YOUR_CONVERTAPI_SECRET"

# Baixar o arquivo DOCX
response = requests.get(docx_url)
if response.status_code == 200:
    files = {
        'File': ('document.docx', response.content)
    }
    # Enviar o arquivo para a API do ConvertAPI
    convert_response = requests.post(convertapi_url, files=files)
    if convert_response.status_code == 200:
        result = convert_response.json()
        pdf_url = result['Files'][0]['Url']
        # Baixar o PDF gerado
        pdf_response = requests.get(pdf_url)
        if pdf_response.status_code == 200:
            # Exibir botão de download no Streamlit
            st.download_button(
                label="📥 Baixar Proposta em PDF",
                data=pdf_response.content,
                file_name="Proposta_Comercial.pdf",
                mime="application/pdf"
            )
        else:
            st.error("Erro ao baixar o PDF gerado.")
    else:
        st.error("Erro na conversão do DOCX para PDF.")
else:
    st.error("Erro ao baixar o documento DOCX.")
