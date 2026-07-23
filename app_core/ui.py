from __future__ import annotations

import base64
import html
from pathlib import Path
from typing import Any

import streamlit as st

from app_core.settings import get_default_branding, normalize_branding

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LOGO = ROOT / "imgs" / "logo.png"
DEFAULT_ICON = ROOT / "imgs" / "v-c.png"


def configure_page(title: str, *, layout: str = "wide") -> None:
    st.set_page_config(
        page_title=title,
        page_icon=str(DEFAULT_ICON) if DEFAULT_ICON.exists() else "ST",
        layout=layout,
        initial_sidebar_state="expanded",
        menu_items={
            "Get help": None,
            "Report a bug": None,
            "About": "Plataforma interna de simulação comercial e análise operacional.",
        },
    )


def get_branding() -> dict[str, Any]:
    try:
        import user_management_db as db

        return normalize_branding(db.get_system_settings())
    except Exception:
        return get_default_branding()


def get_logo_bytes(branding: dict[str, Any] | None = None) -> bytes | None:
    branding = branding or get_branding()
    encoded = branding.get("logo_base64")
    if encoded:
        try:
            return base64.b64decode(encoded)
        except Exception:
            pass
    try:
        return DEFAULT_LOGO.read_bytes()
    except OSError:
        return None


def apply_branding(branding: dict[str, Any] | None = None) -> dict[str, Any]:
    branding = normalize_branding(branding or get_branding())
    css = f"""
    <style>
      :root {{
        --app-primary: {branding['primary_color']};
        --app-secondary: {branding['secondary_color']};
        --app-accent: {branding['accent_color']};
        --app-background: {branding['background_color']};
        --app-surface: {branding['surface_color']};
        --app-text: {branding['text_color']};
        --app-muted: {branding['muted_color']};
        --app-border: color-mix(in srgb, {branding['muted_color']} 22%, transparent);
      }}

      .stApp {{
        background: var(--app-background);
        color: var(--app-text);
      }}

      [data-testid="stHeader"] {{
        background: color-mix(in srgb, var(--app-background) 92%, transparent);
        border-bottom: 1px solid var(--app-border);
      }}

      [data-testid="stSidebar"] {{
        background: var(--app-secondary);
        border-right: 1px solid color-mix(in srgb, white 12%, transparent);
      }}

      [data-testid="stSidebar"] * {{
        color: #F8FAFC;
      }}

      [data-testid="stSidebar"] .stButton button,
      [data-testid="stSidebar"] [data-testid="stPageLink-NavLink"] {{
        border-radius: 10px;
      }}

      [data-testid="stSidebar"] [data-testid="stPageLink-NavLink"]:hover {{
        background: color-mix(in srgb, var(--app-primary) 35%, transparent);
      }}

      .block-container {{
        max-width: 1480px;
        padding-top: 2rem;
        padding-bottom: 4rem;
      }}

      h1, h2, h3, h4 {{
        color: var(--app-text);
        letter-spacing: -0.02em;
      }}

      h1 {{
        font-weight: 750;
      }}

      p, label, .stCaption {{
        color: var(--app-text);
      }}

      [data-testid="stMetric"],
      [data-testid="stForm"],
      [data-testid="stExpander"],
      [data-testid="stDataFrame"],
      [data-testid="stFileUploaderDropzone"],
      div[data-baseweb="tab-list"] {{
        background: var(--app-surface);
        border: 1px solid var(--app-border);
        border-radius: 14px;
      }}

      [data-testid="stMetric"] {{
        padding: 1rem 1.1rem;
        box-shadow: 0 8px 24px rgba(15, 23, 42, 0.05);
      }}

      [data-testid="stMetricValue"] {{
        color: var(--app-secondary);
        font-weight: 750;
      }}

      .stButton > button,
      .stDownloadButton > button,
      [data-testid="stFormSubmitButton"] > button {{
        border-radius: 10px;
        min-height: 2.75rem;
        font-weight: 650;
        border: 1px solid var(--app-border);
      }}

      .stButton > button[kind="primary"],
      .stDownloadButton > button[kind="primary"],
      [data-testid="stFormSubmitButton"] > button[kind="primary"] {{
        background: var(--app-primary);
        border-color: var(--app-primary);
        color: white;
      }}

      .stTextInput input,
      .stNumberInput input,
      .stTextArea textarea,
      div[data-baseweb="select"] > div {{
        border-radius: 10px;
      }}

      div[data-baseweb="tab-highlight"] {{
        background-color: var(--app-primary);
      }}

      .app-hero {{
        background: linear-gradient(135deg, var(--app-secondary), color-mix(in srgb, var(--app-primary) 72%, var(--app-secondary)));
        border-radius: 18px;
        padding: 1.6rem 1.8rem;
        margin-bottom: 1.4rem;
        color: white;
        box-shadow: 0 16px 40px rgba(15, 23, 42, 0.14);
      }}

      .app-hero h1, .app-hero p {{
        color: white;
        margin: 0;
      }}

      .app-hero p {{
        opacity: .82;
        margin-top: .4rem;
      }}

      .app-card {{
        background: var(--app-surface);
        border: 1px solid var(--app-border);
        border-radius: 14px;
        padding: 1.1rem 1.2rem;
        min-height: 100%;
        box-shadow: 0 8px 24px rgba(15, 23, 42, 0.045);
      }}

      .app-card-title {{
        font-size: .84rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: .06em;
        color: var(--app-muted);
      }}

      .app-card-value {{
        font-size: 1.65rem;
        font-weight: 760;
        color: var(--app-secondary);
        margin-top: .3rem;
      }}

      .app-muted {{ color: var(--app-muted); }}
      .app-divider {{ border-top: 1px solid var(--app-border); margin: 1.25rem 0; }}

      #MainMenu {{ visibility: hidden; }}
      footer {{ visibility: hidden; }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)
    return branding


def render_logo(*, sidebar: bool = False, max_width: int = 250) -> None:
    logo = get_logo_bytes()
    if not logo:
        return
    target = st.sidebar if sidebar else st
    target.image(logo, width=max_width)


def render_hero(title: str, subtitle: str | None = None) -> None:
    safe_title = html.escape(str(title))
    safe_subtitle = html.escape(str(subtitle or ""))
    st.markdown(
        f"""
        <section class="app-hero">
          <h1>{safe_title}</h1>
          <p>{safe_subtitle}</p>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar(*, current_page: str | None = None, include_logout: bool = True) -> None:
    branding = get_branding()
    render_logo(sidebar=True, max_width=180)
    st.sidebar.markdown(f"### {branding['system_name']}")
    st.sidebar.caption(branding["system_subtitle"])

    if st.session_state.get("authentication_status"):
        st.sidebar.markdown("---")
        st.sidebar.caption("Sessão atual")
        st.sidebar.markdown(f"**{st.session_state.get('name', 'Usuário')}**")
        role_label = "Administrador" if st.session_state.get("role") == "admin" else "Usuário"
        st.sidebar.caption(role_label)

        st.sidebar.markdown("---")
        st.sidebar.caption("Navegação")
        st.sidebar.page_link("Simulador_Comercial.py", label="Visão geral")
        st.sidebar.page_link("pages/1_Simulador_PJ.py", label="Simulador PJ")
        st.sidebar.page_link("pages/2_Simulador_PF.py", label="Simulador PF")
        st.sidebar.page_link("pages/3_Simulador_Licitacao.py", label="Licitações e editais")
        st.sidebar.page_link("pages/4_Dashboard.py", label="Dashboard de propostas")
        st.sidebar.page_link("pages/5_Consultas_Gerais.py", label="Consultas gerais")
        st.sidebar.page_link("pages/6_Analise_Jornada.py", label="Análise de jornada")
        st.sidebar.page_link("pages/7_Pesquisa_Mercado.py", label="Pesquisa de mercado")
        st.sidebar.page_link("pages/8_Dados_Clientes.py", label="Dados de clientes")
        st.sidebar.page_link("pages/9_Gestao_Estoque.py", label="Gestão de estoque")
        st.sidebar.page_link("pages/10_Comandos_Rastreadores.py", label="Comandos de rastreadores")
        st.sidebar.page_link("pages/11_Analise_Terminais.py", label="Análise de terminais")

        if st.session_state.get("role") == "admin":
            st.sidebar.markdown("---")
            st.sidebar.caption("Administração")
            st.sidebar.page_link("pages/90_Logs.py", label="Auditoria e logs")

        st.sidebar.markdown("---")
        st.sidebar.page_link("pages/99_Ajuda.py", label="Ajuda e documentação")

        if include_logout:
            try:
                from app_core.auth import build_authenticator

                authenticator, _ = build_authenticator()
                authenticator.logout("Sair", "sidebar", key="sidebar_logout")
            except Exception:
                pass

    footer = branding.get("footer_text")
    if footer:
        st.sidebar.markdown("---")
        st.sidebar.caption(footer)


def page_shell(title: str, subtitle: str) -> dict[str, Any]:
    branding = apply_branding()
    render_sidebar()
    render_hero(title, subtitle)
    return branding


def money(value: Any) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = 0.0
    return f"R$ {number:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
