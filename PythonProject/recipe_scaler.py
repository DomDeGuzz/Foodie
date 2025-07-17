import re
from fractions import Fraction

def parse_ingredient_string(raw: str):
    ingredients = []
    for item in raw.split(','):
        item = item.strip()
        if ':' not in item:
            continue

        name, qty_unit_raw = item.split(':', 1)
        name = name.strip()

        match = re.match(r'([\d\s\/\.]+)([a-zA-Z]+)', qty_unit_raw.strip())
        if not match:
            continue

        qty_str, unit = match.groups()
        try:
            quantity = float(Fraction(qty_str.strip()))
        except Exception:
            quantity = 0

        ingredients.append({
            "name": name,
            "quantity": quantity,
            "unit": unit.strip()
        })

    return ingredients


def scale_ingredients(ingredients, original_servings, desired_servings):

    try:
        original = float(original_servings)
        desired = float(desired_servings)
        multiplier = desired / original
    except Exception:
        multiplier = 1

    scaled = []
    for ing in ingredients:
        quantity = ing.get("quantity", 0)
        scaled_qty = round(quantity * multiplier, 2)

        scaled.append({
            "name": ing.get("name", ""),
            "unit": ing.get("unit", ""),
            "original_quantity": quantity,
            "scaled_quantity": scaled_qty
        })

    return scaled
