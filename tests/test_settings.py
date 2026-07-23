from app_core.settings import branding_contrast_errors, contrast_ratio, normalize_branding


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


def test_low_contrast_branding_is_rejected():
    errors = branding_contrast_errors(
        {
            "text_color": "#FFFFFF",
            "background_color": "#FFFFFF",
            "surface_color": "#FFFFFF",
            "secondary_color": "#FFFFFF",
            "primary_color": "#FFFFFF",
        }
    )
    assert len(errors) >= 3
