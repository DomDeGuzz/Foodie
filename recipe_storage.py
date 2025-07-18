import json
import os

DATA_FILE = "recipes.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def save_recipe(user_id, name, ingredients, servings):
    data = load_data()
    user_key = str(user_id)
    if user_key not in data:
        data[user_key] = {}
    data[user_key][name] = {
        "ingredients": ingredients,
        "servings": servings
    }
    save_data(data)

def get_recipe(user_id, name):
    data = load_data()
    return data.get(str(user_id), {}).get(name)

def list_recipes(user_id):
    data = load_data()
    return list(data.get(str(user_id), {}).keys())

def delete_recipe(user_id, name):
    data = load_data()
    user_key = str(user_id)
    if user_key in data and name in data[user_key]:
        del data[user_key][name]
        save_data(data)
        return True
    return False



