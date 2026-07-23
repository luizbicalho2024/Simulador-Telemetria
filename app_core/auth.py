from __future__ import annotations

from typing import Any

import streamlit as st
import streamlit_authenticator as stauth

import user_management_db as db

LOGIN_FIELDS = {
    "Form name": "Acesso à plataforma",
    "Username": "Usuário",
    "Password": "Senha",
    "Login": "Entrar",
}


def build_authenticator() -> tuple[Any, dict]:
    credentials = db.fetch_all_users_for_auth()
    cookie_name = str(st.secrets.get("AUTH_COOKIE_NAME", "simulador_telemetria_auth")).strip()
    cookie_key = str(st.secrets.get("AUTH_COOKIE_KEY", "")).strip()
    if len(cookie_key) < 32:
        raise RuntimeError("AUTH_COOKIE_KEY deve possuir pelo menos 32 caracteres.")

    authenticator = stauth.Authenticate(
        credentials,
        cookie_name,
        cookie_key,
        cookie_expiry_days=int(st.secrets.get("AUTH_COOKIE_EXPIRY_DAYS", 30)),
        pre_authorized=None,
    )
    return authenticator, credentials


def restore_authentication() -> None:
    """Restaura a sessão pelo cookie ao abrir ou atualizar uma página interna."""
    if st.session_state.get("authentication_status"):
        return

    try:
        authenticator, _ = build_authenticator()
        authenticator.login(location="unrendered", key="background_login", max_login_attempts=5)
    except Exception:
        return

    username = str(st.session_state.get("username") or "").strip().lower()
    if st.session_state.get("authentication_status") and username:
        st.session_state["username"] = username
        st.session_state["role"] = db.get_user_role(username) or "user"


def require_auth(role: str | None = None) -> None:
    restore_authentication()

    if not st.session_state.get("authentication_status"):
        st.error("Acesso restrito. Entre novamente pela página inicial.")
        if st.button("Ir para o login", width="content"):
            st.switch_page("Simulador_Comercial.py")
        st.stop()

    username = str(st.session_state.get("username") or "").strip().lower()
    current_role = db.get_user_role(username) if username else None
    if current_role is None:
        clear_auth_state()
        st.error("A conta está inativa ou não existe mais. Entre novamente.")
        st.stop()

    st.session_state["username"] = username
    st.session_state["role"] = current_role

    if role and current_role != role:
        st.error("Seu perfil não possui permissão para acessar esta página.")
        st.stop()


def clear_auth_state() -> None:
    keys = (
        "authentication_status",
        "name",
        "username",
        "role",
        "logged_in_log",
        "logout",
    )
    for key in keys:
        st.session_state.pop(key, None)
