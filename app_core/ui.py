from __future__ import annotations

import base64
import html
from pathlib import Path
from typing import Any

import streamlit as st

from app_core.settings import (
    get_default_branding,
    normalize_branding,
    resolve_branding_colors,
)

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


def _logo_storage_fields(*, sidebar: bool) -> tuple[str, str, str]:
    if sidebar:
        return (
            "sidebar_logo_base64",
            "sidebar_logo_mime",
            "sidebar_logo_filename",
        )
    return "logo_base64", "logo_mime", "logo_filename"


def get_logo_bytes(
    branding: dict[str, Any] | None = None,
    *,
    sidebar: bool = False,
) -> bytes | None:
    """Retorna a logo adequada ao contexto sem adicionar fundos artificiais.

    A sidebar possui uma imagem independente. Enquanto ela não for cadastrada,
    o sistema reutiliza a logo principal para manter compatibilidade com os
    dados já existentes no MongoDB.
    """
    branding = normalize_branding(branding or get_branding())
    base64_field, _, _ = _logo_storage_fields(sidebar=sidebar)
    encoded = branding.get(base64_field)

    if sidebar and not encoded:
        encoded = branding.get("logo_base64")

    if encoded:
        try:
            return base64.b64decode(encoded, validate=True)
        except Exception:
            pass

    try:
        return DEFAULT_LOGO.read_bytes()
    except OSError:
        return None


def get_logo_mime(
    branding: dict[str, Any] | None = None,
    *,
    sidebar: bool = False,
) -> str:
    branding = normalize_branding(branding or get_branding())
    _, mime_field, _ = _logo_storage_fields(sidebar=sidebar)
    mime = branding.get(mime_field)
    if sidebar and not branding.get("sidebar_logo_base64"):
        mime = branding.get("logo_mime")
    return str(mime or "image/png")


def apply_branding(branding: dict[str, Any] | None = None) -> dict[str, Any]:
    branding = normalize_branding(branding or get_branding())
    resolved = resolve_branding_colors(branding)

    css = f"""
    <style>
      :root {{
        --app-primary: {branding['primary_color']};
        --app-secondary: {branding['secondary_color']};
        --app-accent: {branding['accent_color']};
        --app-background: {branding['background_color']};
        --app-surface: {branding['surface_color']};
        --app-text: {resolved['text']};
        --app-surface-text: {resolved['surface_text']};
        --app-muted: {resolved['muted']};
        --app-surface-muted: {resolved['surface_muted']};
        --app-on-primary: {resolved['on_primary']};
        --app-on-secondary: {resolved['on_secondary']};
        --app-on-accent: {resolved['on_accent']};
        --app-sidebar: {branding['sidebar_background_color']};
        --app-sidebar-text: {resolved['sidebar_text']};
        --app-sidebar-muted: {resolved['sidebar_muted']};
        --app-sidebar-hover: {branding['sidebar_hover_color']};
        --app-sidebar-hover-text: {resolved['sidebar_hover_text']};
        --app-sidebar-active: {branding['sidebar_active_color']};
        --app-sidebar-active-text: {resolved['sidebar_active_text']};
        --app-border: color-mix(in srgb, {resolved['surface_muted']} 24%, transparent);
      }}

      html, body, [data-testid="stAppViewContainer"], .stApp {{
        background: var(--app-background);
        color: var(--app-text);
      }}

      [data-testid="stHeader"] {{
        background: color-mix(in srgb, var(--app-background) 94%, transparent);
        border-bottom: 1px solid var(--app-border);
      }}

      [data-testid="stHeader"] button,
      [data-testid="stToolbar"] button {{
        color: var(--app-text) !important;
      }}

      [data-testid="stSidebar"] {{
        background: var(--app-sidebar);
        border-right: 1px solid color-mix(in srgb, var(--app-sidebar-text) 14%, transparent);
      }}

      [data-testid="stSidebar"] h1,
      [data-testid="stSidebar"] h2,
      [data-testid="stSidebar"] h3,
      [data-testid="stSidebar"] h4,
      [data-testid="stSidebar"] h5,
      [data-testid="stSidebar"] h6,
      [data-testid="stSidebar"] p,
      [data-testid="stSidebar"] label,
      [data-testid="stSidebar"] span {{
        color: var(--app-sidebar-text);
      }}

      [data-testid="stSidebar"] [data-testid="stCaptionContainer"] p,
      [data-testid="stSidebar"] .stCaption p {{
        color: var(--app-sidebar-muted) !important;
      }}

      [data-testid="stSidebar"] hr {{
        border-color: color-mix(in srgb, var(--app-sidebar-text) 18%, transparent);
      }}

      [data-testid="stSidebar"] [data-testid="stPageLink-NavLink"] {{
        border-radius: 10px;
        color: var(--app-sidebar-text) !important;
        background: transparent !important;
        transition: background-color .16s ease, color .16s ease, transform .16s ease;
      }}

      [data-testid="stSidebar"] [data-testid="stPageLink-NavLink"] * {{
        color: inherit !important;
      }}

      [data-testid="stSidebar"] [data-testid="stPageLink-NavLink"]:hover {{
        background: var(--app-sidebar-hover) !important;
        color: var(--app-sidebar-hover-text) !important;
        transform: translateX(2px);
      }}

      [data-testid="stSidebar"] [data-testid="stPageLink-NavLink"][aria-current="page"],
      [data-testid="stSidebar"] a[aria-current="page"] {{
        background: var(--app-sidebar-active) !important;
        color: var(--app-sidebar-active-text) !important;
        font-weight: 700 !important;
      }}

      [data-testid="stSidebar"] .stButton > button {{
        width: 100%;
        min-height: 2.55rem;
        border-radius: 10px;
        background: color-mix(in srgb, var(--app-primary) 22%, transparent) !important;
        border: 1px solid color-mix(in srgb, var(--app-sidebar-text) 22%, transparent) !important;
        color: var(--app-sidebar-text) !important;
        font-weight: 700;
      }}

      [data-testid="stSidebar"] .stButton > button:hover {{
        background: var(--app-primary) !important;
        color: var(--app-on-primary) !important;
        border-color: var(--app-primary) !important;
      }}

      .block-container {{
        max-width: 1480px;
        padding-top: 2rem;
        padding-bottom: 4rem;
      }}

      h1, h2, h3, h4, h5, h6 {{
        color: var(--app-text);
        letter-spacing: -0.02em;
      }}

      h1 {{ font-weight: 750; }}

      p, label, .stCaption, [data-testid="stMarkdownContainer"] {{
        color: var(--app-text);
      }}

      a {{ color: var(--app-primary); }}

      [data-testid="stMetric"],
      [data-testid="stForm"],
      [data-testid="stExpander"],
      [data-testid="stDataFrame"],
      [data-testid="stFileUploaderDropzone"],
      div[data-baseweb="tab-list"] {{
        background: var(--app-surface);
        color: var(--app-surface-text);
        border: 1px solid var(--app-border);
        border-radius: 14px;
      }}

      [data-testid="stMetric"] {{
        padding: 1rem 1.1rem;
        box-shadow: 0 8px 24px rgba(15, 23, 42, 0.05);
      }}

      [data-testid="stMetricLabel"] p {{ color: var(--app-surface-muted); }}
      [data-testid="stMetricValue"] {{
        color: var(--app-surface-text);
        font-weight: 750;
      }}

      .stButton > button,
      .stDownloadButton > button,
      [data-testid="stFormSubmitButton"] > button {{
        border-radius: 10px;
        min-height: 2.75rem;
        font-weight: 650;
        border: 1px solid var(--app-border);
        background: var(--app-surface);
        color: var(--app-surface-text);
      }}

      .stButton > button:hover,
      .stDownloadButton > button:hover,
      [data-testid="stFormSubmitButton"] > button:hover {{
        border-color: var(--app-primary);
        color: var(--app-primary);
      }}

      .stButton > button[kind="primary"],
      .stDownloadButton > button[kind="primary"],
      [data-testid="stFormSubmitButton"] > button[kind="primary"] {{
        background: var(--app-primary) !important;
        border-color: var(--app-primary) !important;
        color: var(--app-on-primary) !important;
      }}

      .stButton > button[kind="primary"]:hover,
      .stDownloadButton > button[kind="primary"]:hover,
      [data-testid="stFormSubmitButton"] > button[kind="primary"]:hover {{
        background: color-mix(in srgb, var(--app-primary) 86%, black) !important;
        color: var(--app-on-primary) !important;
      }}

      .stTextInput input,
      .stNumberInput input,
      .stTextArea textarea,
      div[data-baseweb="select"] > div {{
        border-radius: 10px;
        background: var(--app-surface);
        color: var(--app-surface-text);
      }}

      .stTextInput input:focus,
      .stNumberInput input:focus,
      .stTextArea textarea:focus {{
        border-color: var(--app-primary) !important;
        box-shadow: 0 0 0 1px var(--app-primary) !important;
      }}

      div[data-baseweb="tab-highlight"] {{ background-color: var(--app-primary); }}
      button[data-baseweb="tab"][aria-selected="true"] {{ color: var(--app-primary); }}

      [data-testid="stProgress"] > div > div > div,
      [data-testid="stSlider"] [role="slider"] {{
        background-color: var(--app-primary) !important;
      }}

      .app-logo-shell {{
        display: flex;
        align-items: center;
        justify-content: flex-start;
        width: fit-content;
        max-width: 100%;
        box-sizing: border-box;
        overflow: hidden;
      }}

      .app-logo-shell img {{
        display: block;
        width: auto;
        height: auto;
        max-width: 100%;
        max-height: 145px;
        object-fit: contain;
      }}

      .app-logo-shell--sidebar {{
        margin: .2rem 0 1rem;
      }}

      .app-logo-shell--content {{
        margin: .25rem 0 1rem;
      }}

      .app-session-card {{
        border: 1px solid color-mix(in srgb, var(--app-sidebar-text) 15%, transparent);
        background: color-mix(in srgb, var(--app-sidebar-text) 6%, transparent);
        border-radius: 12px;
        padding: .8rem .9rem;
        margin: .55rem 0 .65rem;
      }}

      .app-session-name {{
        color: var(--app-sidebar-text);
        font-weight: 750;
        line-height: 1.25;
      }}

      .app-session-role {{
        color: var(--app-sidebar-muted);
        font-size: .82rem;
        margin-top: .2rem;
      }}

      .app-hero {{
        background: linear-gradient(
          135deg,
          var(--app-secondary),
          color-mix(in srgb, var(--app-primary) 72%, var(--app-secondary))
        );
        border-radius: 18px;
        padding: 1.6rem 1.8rem;
        margin-bottom: 1.4rem;
        color: var(--app-on-secondary);
        box-shadow: 0 16px 40px rgba(15, 23, 42, 0.14);
      }}

      .app-hero h1, .app-hero p {{
        color: var(--app-on-secondary) !important;
        margin: 0;
      }}

      .app-hero p {{ opacity: .86; margin-top: .4rem; }}

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
        color: var(--app-surface-muted);
      }}

      .app-card-value {{
        font-size: 1.65rem;
        font-weight: 760;
        color: var(--app-surface-text);
        margin-top: .3rem;
      }}

      .app-muted {{ color: var(--app-surface-muted); }}
      .app-divider {{ border-top: 1px solid var(--app-border); margin: 1.25rem 0; }}

      #MainMenu {{ visibility: hidden; }}
      footer {{ visibility: hidden; }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)
    return branding


def render_logo(
    *,
    sidebar: bool = False,
    max_width: int = 250,
    branding: dict[str, Any] | None = None,
) -> None:
    """Renderiza a logo principal ou a logo da sidebar com transparência real."""
    branding = normalize_branding(branding or get_branding())
    logo = get_logo_bytes(branding, sidebar=sidebar)
    if not logo:
        return

    mime = get_logo_mime(branding, sidebar=sidebar)
    encoded = base64.b64encode(logo).decode("ascii")
    panel_class = "app-logo-shell--sidebar" if sidebar else "app-logo-shell--content"
    safe_width = max(80, min(int(max_width), 700))
    alt = "Logomarca da barra lateral" if sidebar else "Logomarca principal do sistema"

    markup = f"""
    <div class="app-logo-shell {panel_class}"
         style="width:min(100%, {safe_width}px);">
      <img src="data:{html.escape(mime)};base64,{encoded}"
           alt="{html.escape(alt)}"
           style="max-width:{safe_width}px;" />
    </div>
    """
    target = st.sidebar if sidebar else st
    target.markdown(markup, unsafe_allow_html=True)


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
    render_logo(sidebar=True, max_width=210, branding=branding)
    st.sidebar.markdown(f"### {html.escape(branding['system_name'])}")
    st.sidebar.caption(branding["system_subtitle"])

    if st.session_state.get("authentication_status"):
        st.sidebar.markdown("---")
        st.sidebar.caption("Sessão atual")
        role_label = "Administrador" if st.session_state.get("role") == "admin" else "Usuário"
        safe_name = html.escape(str(st.session_state.get("name", "Usuário")))
        st.sidebar.markdown(
            f"""
            <div class="app-session-card">
              <div class="app-session-name">{safe_name}</div>
              <div class="app-session-role">{role_label}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # O logout fica imediatamente abaixo da sessão, permanecendo visível
        # mesmo quando a lista de páginas é longa.
        if include_logout:
            try:
                from app_core.auth import build_authenticator

                authenticator, _ = build_authenticator()
                logout_key = "sidebar_logout"
                if current_page:
                    normalized_page = "".join(
                        character if character.isalnum() else "_"
                        for character in str(current_page)
                    )
                    logout_key = f"sidebar_logout_{normalized_page}"
                authenticator.logout("Sair da plataforma", "sidebar", key=logout_key)
            except Exception:
                st.sidebar.caption("Não foi possível carregar o encerramento de sessão.")

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

    footer = branding.get("footer_text")
    if footer:
        st.sidebar.markdown("---")
        st.sidebar.caption(footer)


def page_shell(title: str, subtitle: str) -> dict[str, Any]:
    branding = apply_branding()
    render_sidebar(current_page=title)
    render_hero(title, subtitle)
    return branding


def money(value: Any) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = 0.0
    return f"R$ {number:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
