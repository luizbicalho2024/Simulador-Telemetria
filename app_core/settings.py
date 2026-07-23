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
    "logo_base64": None,
    "logo_mime": None,
    "logo_filename": None,
    "footer_text": "Uso interno",
}

HEX_COLOR_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")


def get_default_branding() -> dict[str, Any]:
    return deepcopy(DEFAULT_BRANDING)


def normalize_hex(value: str | None, fallback: str) -> str:
    value = (value or "").strip()
    return value.upper() if HEX_COLOR_RE.fullmatch(value) else fallback


def normalize_branding(data: dict[str, Any] | None) -> dict[str, Any]:
    result = get_default_branding()
    if data:
        result.update({k: v for k, v in data.items() if k in result})

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

    result["system_name"] = str(result.get("system_name") or DEFAULT_BRANDING["system_name"]).strip()[:80]
    result["system_subtitle"] = str(result.get("system_subtitle") or DEFAULT_BRANDING["system_subtitle"]).strip()[:160]
    result["footer_text"] = str(result.get("footer_text") or "").strip()[:160]
    return result



def _hex_to_rgb(value: str) -> tuple[int, int, int]:
    normalized = normalize_hex(value, "#000000").lstrip("#")
    return tuple(int(normalized[index:index + 2], 16) for index in (0, 2, 4))


def _relative_luminance(value: str) -> float:
    channels = []
    for channel in _hex_to_rgb(value):
        normalized = channel / 255
        channels.append(normalized / 12.92 if normalized <= 0.04045 else ((normalized + 0.055) / 1.055) ** 2.4)
    red, green, blue = channels
    return 0.2126 * red + 0.7152 * green + 0.0722 * blue


def contrast_ratio(first: str, second: str) -> float:
    luminance_1 = _relative_luminance(first)
    luminance_2 = _relative_luminance(second)
    lighter = max(luminance_1, luminance_2)
    darker = min(luminance_1, luminance_2)
    return (lighter + 0.05) / (darker + 0.05)


def branding_contrast_errors(data: dict[str, Any]) -> list[str]:
    branding = normalize_branding(data)
    checks = (
        ("texto e fundo", branding["text_color"], branding["background_color"], 4.5),
        ("texto e superfície", branding["text_color"], branding["surface_color"], 4.5),
        ("texto branco e barra lateral", "#FFFFFF", branding["secondary_color"], 4.5),
        ("texto branco e cor primária", "#FFFFFF", branding["primary_color"], 3.0),
    )
    errors = []
    for label, foreground, background, minimum in checks:
        ratio = contrast_ratio(foreground, background)
        if ratio < minimum:
            errors.append(f"Contraste insuficiente entre {label}: {ratio:.2f}:1; mínimo recomendado {minimum:.1f}:1.")
    return errors
