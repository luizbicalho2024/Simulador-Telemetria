import streamlit as st

# 🛠️ Configuração da página
st.set_page_config(
    layout="wide",
    page_title="Simulador Comercial Verdio",
    page_icon="imgs/v-c.png",
    initial_sidebar_state="expanded"
)

# 🔵 Logotipo e cabeçalho estilizado
st.image("imgs/logo.png", width=250)
st.markdown("<h1 style='text-align: center; color: #54A033;'>Bem Vindo ao Simulador Verdio</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center; color: #000;'>Comandos - Licitação - Pessoa Física - Pessoa Jurídica</h3>", unsafe_allow_html=True)
st.markdown("---")
st.markdown(
    """
    <div style="display: flex; justify-content: center;">
        <img src="imgs/bannerverdio.png" width="900">
    </div>
    """,
    unsafe_allow_html=True
)
