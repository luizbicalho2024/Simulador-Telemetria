import streamlit as st
import time

# 🛠️ Configuração da página
st.set_page_config(
    layout="wide",
    page_title="Simulador Comercial Verdio",
    page_icon="imgs/v-c.png",
    initial_sidebar_state="expanded"
)

logo = ("imgs/logo.png")
st.logo(logo)
st.image("imgs/logo.png", width=200, output_format="auto",  caption="")
st.markdown("## Bem Vindo ao Simulador Verdio")
st.image("imgs/bannerverdio.png", width=900, output_format="auto",  caption="")