import streamlit as st
import time

# 🛠️ Configuração da página
st.set_page_config(
    layout="wide",
    page_title="Simulador Comercial Verdio",
    page_icon="imgs/v-c.png",
    initial_sidebar_state="expanded"
)

'''logo = ("imgs/logo.png")
st.logo(logo)
st.image("imgs/logo.png", width=200, output_format="auto",  caption="")
st.markdown("## Bem Vindo ao Simulador Verdio")'''
# 🔵 Logotipo e cabeçalho estilizado
st.image("imgs/logo.png", width=250)
st.markdown("<h1 style='text-align: center; color: #54A033;'>Bem Vindo ao Simulador Verdio</h1>", unsafe_allow_html=True)
st.markdown("#### Comandos - Licitação - Pessoa Física - Pessoa Jurídica")
st.markdown("---")
st.image("imgs/bannerverdio.png", width=900, output_format="auto",  caption="")