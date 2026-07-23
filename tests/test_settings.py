from app_core.settings import (
    best_contrast_text,
    branding_contrast_errors,
    contrast_ratio,
    normalize_branding,
    resolve_branding_colors,
)


def test_normalize_branding_rejects_invalid_color_and_limits_text():
    branding = normalize_branding(
        {
            "system_name": "A" * 200,
            "primary_color": "blue",
            "secondary_color": "#112233",
        }
    )
    assert len(branding["system_name"]) == 80
    assert branding["primary_color"] == "#165DFF"
    assert branding["secondary_color"] == "#112233"


def test_default_branding_has_acceptable_contrast():
    assert branding_contrast_errors(normalize_branding(None)) == []
    assert contrast_ratio("#000000", "#FFFFFF") == 21.0


def test_low_contrast_branding_generates_warnings():
    errors = branding_contrast_errors(
        {
            "text_color": "#FFFFFF",
            "background_color": "#FFFFFF",
            "surface_color": "#FFFFFF",
            "secondary_color": "#FFFFFF",
            "primary_color": "#FFFFFF",
            "sidebar_background_color": "#FFFFFF",
            "sidebar_text_color": "#FFFFFF",
            "sidebar_active_color": "#FFFFFF",
            "sidebar_active_text_color": "#FFFFFF",
        }
    )
    assert len(errors) >= 3


def test_automatic_contrast_keeps_light_primary_color_readable():
    resolved = resolve_branding_colors(
        {
            "primary_color": "#FFD000",
            "auto_contrast": True,
        }
    )
    assert resolved["on_primary"] == "#111827"
    assert best_contrast_text("#FFD000") == "#111827"


def test_previous_branding_migrates_sidebar_from_existing_colors():
    branding = normalize_branding(
        {
            "primary_color": "#FF5C1A",
            "secondary_color": "#2D2926",
        }
    )
    assert branding["sidebar_background_color"] == "#2D2926"
    assert branding["sidebar_hover_color"] == "#FF5C1A"
    assert branding["sidebar_active_color"] == "#FF5C1A"

def test_branding_supports_independent_sidebar_logo():
    branding = normalize_branding({"logo_base64": "MAIN", "sidebar_logo_base64": "SIDE"})
    assert branding["logo_base64"] == "MAIN"
    assert branding["sidebar_logo_base64"] == "SIDE"


def test_old_branding_document_receives_sidebar_defaults():
    branding = normalize_branding({"secondary_color": "#112233", "primary_color": "#445566"})
    assert branding["sidebar_background_color"] == "#112233"
    assert branding["sidebar_hover_color"] == "#445566"
    assert "sidebar_logo_base64" in branding
