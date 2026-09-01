import ast
from pathlib import Path


def test_product_cards_remain_inside_products_loop() -> None:
    source = Path("pages/1_Simulador_PJ.py").read_text(
        encoding="utf-8"
    )
    tree = ast.parse(source)

    product_loop = None
    for node in tree.body:
        if not isinstance(node, ast.For):
            continue
        if not isinstance(node.target, ast.Tuple):
            continue
        names = [
            element.id
            for element in node.target.elts
            if isinstance(element, ast.Name)
        ]
        if names == ["product", "base_price"]:
            product_loop = node
            break

    assert product_loop is not None

    assigned_names: set[str] = set()
    has_product_toggle = False
    has_quantity_input = False
    has_selected_assignment = False

    for node in ast.walk(product_loop):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    assigned_names.add(target.id)
                if (
                    isinstance(target, ast.Subscript)
                    and isinstance(target.value, ast.Name)
                    and target.value.id == "selected"
                ):
                    has_selected_assignment = True

        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute):
                if node.func.attr == "toggle":
                    has_product_toggle = True
                elif node.func.attr == "number_input":
                    has_quantity_input = True

    assert "effective_price" in assigned_names
    assert "pricing_mode" in assigned_names
    assert "quantity" in assigned_names
    assert has_product_toggle
    assert has_quantity_input
    assert has_selected_assignment


def test_post_loop_empty_selection_guard_stays_outside_loop() -> None:
    source = Path("pages/1_Simulador_PJ.py").read_text(
        encoding="utf-8"
    )

    assert "\n    effective_price = base_price\n" in source
    assert "\nif not selected:\n" in source
