import json
import os

STORAGE_FILE = "saved_recipes.json"  # Unified constant name

def load_recipes():
    if not os.path.exists(STORAGE_FILE):
        return {}
    with open(STORAGE_FILE, "r") as f:
        return json.load(f)

def save_recipe(name, ingredients, servings):
    data = load_recipes()
    data[name.lower()] = {
        "ingredients": ingredients,
        "servings": servings
    }
    with open(STORAGE_FILE, "w") as f:
        json.dump(data, f, indent=2)

def get_recipe(name):
    data = load_recipes()
    return data.get(name.lower())

def list_recipes():
    return list(load_recipes().keys())

def delete_recipe(name):
    name = name.lower()  # normalize input
    if not os.path.exists(STORAGE_FILE):
        return False

    with open(STORAGE_FILE, "r") as f:
        data = json.load(f)

    if name not in data:
        return False

    del data[name]

    with open(STORAGE_FILE, "w") as f:
        json.dump(data, f, indent=2)

    return True



