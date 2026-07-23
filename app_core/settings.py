from __future__ import annotations

import re
from copy import deepcopy
from typing import Any

DEFAULT_BRANDING: dict[str, Any] = {
    "_id": "global_branding",
    "system_name": "Simulador de Telemetria",
    "system_subtitle": "Inteligência comercial e operacional",
    "primary_color": "#165DFF",
    "secondary_color": "#0B1F33",
    "accent_color": "#00A884",
    "background_color": "#F5F7FA",
    "surface_color": "#FFFFFF",
    "text_color": "#172B4D",
    "muted_color": "#667085",
    "sidebar_background_color": "#0B1F33",
    "sidebar_text_color": "#F8FAFC",
    "sidebar_muted_color": "#CBD5E1",
    "sidebar_hover_color": "#243B53",
    "sidebar_active_color": "#165DFF",
    "sidebar_active_text_color": "#FFFFFF",
    "auto_contrast": True,
    "logo_background_mode": "auto",
    "logo_background_color": "#FFFFFF",
    "logo_padding": 12,
    "logo_border_radius": 12,
    # Logomarca principal: páginas, área de login e pré-visualização administrativa.
    "logo_base64": None,
    "logo_mime": None,
    "logo_filename": None,
    # Logomarca específica da barra lateral. Quando ausente, usa a principal.
    "sidebar_logo_base64": None,
    "sidebar_logo_mime": None,
    "sidebar_logo_filename": None,
    "footer_text": "Uso interno",
}

HEX_COLOR_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")
LOGO_BACKGROUND_MODES = {"auto", "transparent", "custom"}


def get_default_branding() -> dict[str, Any]:
    return deepcopy(DEFAULT_BRANDING)


def normalize_hex(value: str | None, fallback: str) -> str:
    value = (value or "").strip()
    return value.upper() if HEX_COLOR_RE.fullmatch(value) else fallback


def _clamp_int(value: Any, fallback: int, minimum: int, maximum: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        parsed = fallback
    return max(minimum, min(parsed, maximum))


def normalize_branding(data: dict[str, Any] | None) -> dict[str, Any]:
    provided = data or {}
    result = get_default_branding()
    result.update({key: value for key, value in provided.items() if key in result})

    for field in (
        "primary_color",
        "secondary_color",
        "accent_color",
        "background_color",
        "surface_color",
        "text_color",
        "muted_color",
    ):
        result[field] = normalize_hex(result.get(field), DEFAULT_BRANDING[field])

    # Migração transparente das configurações criadas antes da versão 2.1.
    # Quando os novos campos ainda não existem no MongoDB, a sidebar continua
    # respeitando as cores primária e secundária já salvas pelo administrador.
    sidebar_fallbacks = {
        "sidebar_background_color": result["secondary_color"],
        "sidebar_text_color": DEFAULT_BRANDING["sidebar_text_color"],
        "sidebar_muted_color": DEFAULT_BRANDING["sidebar_muted_color"],
        "sidebar_hover_color": result["primary_color"],
        "sidebar_active_color": result["primary_color"],
        "sidebar_active_text_color": DEFAULT_BRANDING["sidebar_active_text_color"],
    }
    for field, fallback in sidebar_fallbacks.items():
        raw_value = provided.get(field) if field in provided else fallback
        result[field] = normalize_hex(raw_value, fallback)

    result["auto_contrast"] = bool(result.get("auto_contrast", True))

    logo_mode = str(result.get("logo_background_mode") or "auto").strip().lower()
    result["logo_background_mode"] = logo_mode if logo_mode in LOGO_BACKGROUND_MODES else "auto"
    result["logo_background_color"] = normalize_hex(
        result.get("logo_background_color"),
        DEFAULT_BRANDING["logo_background_color"],
    )
    result["logo_padding"] = _clamp_int(
        result.get("logo_padding"),
        DEFAULT_BRANDING["logo_padding"],
        0,
        40,
    )
    result["logo_border_radius"] = _clamp_int(
        result.get("logo_border_radius"),
        DEFAULT_BRANDING["logo_border_radius"],
        0,
        40,
    )

    result["system_name"] = str(result.get("system_name") or DEFAULT_BRANDING["system_name"]).strip()[:80]
    result["system_subtitle"] = str(
        result.get("system_subtitle") or DEFAULT_BRANDING["system_subtitle"]
    ).strip()[:160]
    result["footer_text"] = str(result.get("footer_text") or "").strip()[:160]
    return result


def _hex_to_rgb(value: str) -> tuple[int, int, int]:
    normalized = normalize_hex(value, "#000000").lstrip("#")
    return tuple(int(normalized[index:index + 2], 16) for index in (0, 2, 4))


def _relative_luminance(value: str) -> float:
    channels = []
    for channel in _hex_to_rgb(value):
        normalized = channel / 255
        channels.append(
            normalized / 12.92
            if normalized <= 0.04045
            else ((normalized + 0.055) / 1.055) ** 2.4
        )
    red, green, blue = channels
    return 0.2126 * red + 0.7152 * green + 0.0722 * blue


def contrast_ratio(first: str, second: str) -> float:
    luminance_1 = _relative_luminance(first)
    luminance_2 = _relative_luminance(second)
    lighter = max(luminance_1, luminance_2)
    darker = min(luminance_1, luminance_2)
    return (lighter + 0.05) / (darker + 0.05)


def best_contrast_text(background: str) -> str:
    """Retorna preto ou branco, escolhendo o maior contraste com o fundo."""
    white_ratio = contrast_ratio("#FFFFFF", background)
    dark_ratio = contrast_ratio("#111827", background)
    return "#FFFFFF" if white_ratio >= dark_ratio else "#111827"


def ensure_contrast(
    foreground: str,
    background: str,
    *,
    minimum: float = 4.5,
    enabled: bool = True,
) -> str:
    """Mantém a cor escolhida quando legível ou aplica texto automático."""
    normalized_foreground = normalize_hex(foreground, "#111827")
    normalized_background = normalize_hex(background, "#FFFFFF")
    if not enabled or contrast_ratio(normalized_foreground, normalized_background) >= minimum:
        return normalized_foreground
    return best_contrast_text(normalized_background)


def resolve_branding_colors(data: dict[str, Any] | None) -> dict[str, str]:
    """Resolve as cores efetivamente usadas pela interface.

    As escolhas do administrador continuam armazenadas. Quando o contraste
    automático está ativo, apenas as cores de texto que ficariam ilegíveis são
    substituídas em tempo de renderização.
    """
    branding = normalize_branding(data)
    automatic = bool(branding["auto_contrast"])

    return {
        "text": ensure_contrast(
            branding["text_color"],
            branding["background_color"],
            minimum=4.5,
            enabled=automatic,
        ),
        "surface_text": ensure_contrast(
            branding["text_color"],
            branding["surface_color"],
            minimum=4.5,
            enabled=automatic,
        ),
        "muted": ensure_contrast(
            branding["muted_color"],
            branding["background_color"],
            minimum=3.0,
            enabled=automatic,
        ),
        "surface_muted": ensure_contrast(
            branding["muted_color"],
            branding["surface_color"],
            minimum=3.0,
            enabled=automatic,
        ),
        "on_primary": ensure_contrast(
            best_contrast_text(branding["primary_color"]),
            branding["primary_color"],
            minimum=4.5,
            enabled=True,
        ),
        "on_secondary": ensure_contrast(
            best_contrast_text(branding["secondary_color"]),
            branding["secondary_color"],
            minimum=4.5,
            enabled=True,
        ),
        "on_accent": ensure_contrast(
            best_contrast_text(branding["accent_color"]),
            branding["accent_color"],
            minimum=4.5,
            enabled=True,
        ),
        "sidebar_text": ensure_contrast(
            branding["sidebar_text_color"],
            branding["sidebar_background_color"],
            minimum=4.5,
            enabled=automatic,
        ),
        "sidebar_muted": ensure_contrast(
            branding["sidebar_muted_color"],
            branding["sidebar_background_color"],
            minimum=3.0,
            enabled=automatic,
        ),
        "sidebar_active_text": ensure_contrast(
            branding["sidebar_active_text_color"],
            branding["sidebar_active_color"],
            minimum=4.5,
            enabled=automatic,
        ),
        "sidebar_hover_text": ensure_contrast(
            branding["sidebar_text_color"],
            branding["sidebar_hover_color"],
            minimum=4.5,
            enabled=automatic,
        ),
    }


def branding_contrast_errors(data: dict[str, Any]) -> list[str]:
    """Retorna avisos de contraste das cores escolhidas pelo administrador.

    Os avisos não precisam bloquear o salvamento. A interface usa
    ``resolve_branding_colors`` para corrigir automaticamente os textos quando
    ``auto_contrast`` estiver habilitado.
    """
    branding = normalize_branding(data)
    checks = (
        ("texto e fundo", branding["text_color"], branding["background_color"], 4.5),
        ("texto e superfície", branding["text_color"], branding["surface_color"], 4.5),
        (
            "texto da barra lateral e seu fundo",
            branding["sidebar_text_color"],
            branding["sidebar_background_color"],
            4.5,
        ),
        (
            "texto do item ativo e sua cor",
            branding["sidebar_active_text_color"],
            branding["sidebar_active_color"],
            4.5,
        ),
    )
    errors = []
    for label, foreground, background, minimum in checks:
        ratio = contrast_ratio(foreground, background)
        if ratio < minimum:
            errors.append(
                f"Contraste reduzido entre {label}: {ratio:.2f}:1; "
                f"mínimo recomendado {minimum:.1f}:1."
            )
    return errors
