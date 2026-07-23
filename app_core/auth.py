from __future__ import annotations

import hashlib
import json
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

_AUTHENTICATOR_KEY = "_simulador_authenticator"
_AUTHENTICATOR_SIGNATURE_KEY = "_simulador_authenticator_signature"


def _credentials_signature(
    credentials: dict,
    cookie_name: str,
    cookie_key: str,
    cookie_expiry_days: int,
) -> str:
    payload = {
        "credentials": credentials,
        "cookie_name": cookie_name,
        "cookie_key": cookie_key,
        "cookie_expiry_days": cookie_expiry_days,
    }
    serialized = json.dumps(
        payload,
        sort_keys=True,
        ensure_ascii=False,
        default=str,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(serialized).hexdigest()


def build_authenticator() -> tuple[Any, dict]:
    """Cria uma única instância do autenticador por sessão.

    Em aplicações multipágina, reutilizar a mesma instância evita inconsistências
    entre a restauração do cookie e o botão de logout das páginas internas.
    """
    credentials = db.fetch_all_users_for_auth()
    cookie_name = str(st.secrets.get("AUTH_COOKIE_NAME", "simulador_telemetria_auth")).strip()
    cookie_key = str(st.secrets.get("AUTH_COOKIE_KEY", "")).strip()
    cookie_expiry_days = int(st.secrets.get("AUTH_COOKIE_EXPIRY_DAYS", 30))

    if len(cookie_key) < 32:
        raise RuntimeError("AUTH_COOKIE_KEY deve possuir pelo menos 32 caracteres.")

    signature = _credentials_signature(
        credentials,
        cookie_name,
        cookie_key,
        cookie_expiry_days,
    )
    existing = st.session_state.get(_AUTHENTICATOR_KEY)
    existing_signature = st.session_state.get(_AUTHENTICATOR_SIGNATURE_KEY)

    if existing is not None and existing_signature == signature:
        return existing, credentials

    authenticator = stauth.Authenticate(
        credentials,
        cookie_name,
        cookie_key,
        cookie_expiry_days=cookie_expiry_days,
        pre_authorized=None,
    )
    st.session_state[_AUTHENTICATOR_KEY] = authenticator
    st.session_state[_AUTHENTICATOR_SIGNATURE_KEY] = signature
    return authenticator, credentials


def restore_authentication() -> None:
    """Restaura a sessão pelo cookie ao abrir ou atualizar uma página interna."""
    try:
        authenticator, _ = build_authenticator()
    except Exception:
        return

    if not st.session_state.get("authentication_status"):
        try:
            authenticator.login(
                location="unrendered",
                key="background_login",
                max_login_attempts=5,
            )
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


def perform_logout() -> None:
    """Encerra a sessão, remove o cookie e volta para a tela principal."""
    authenticator, _ = build_authenticator()
    try:
        authenticator.logout(location="unrendered")
    finally:
        clear_auth_state(keep_authenticator=False)
    st.switch_page("Simulador_Comercial.py")


def render_logout_button(*, key: str = "global_sidebar_logout") -> None:
    """Renderiza um botão próprio e usa o autenticador apenas para apagar o cookie."""
    if st.sidebar.button(
        "Sair da plataforma",
        key=key,
        use_container_width=True,
    ):
        perform_logout()


def clear_auth_state(*, keep_authenticator: bool = False) -> None:
    keys = (
        "authentication_status",
        "name",
        "username",
        "role",
        "logged_in_log",
        "logout",
        "failed_login_attempts",
    )
    for key in keys:
        st.session_state.pop(key, None)

    if not keep_authenticator:
        st.session_state.pop(_AUTHENTICATOR_KEY, None)
        st.session_state.pop(_AUTHENTICATOR_SIGNATURE_KEY, None)
