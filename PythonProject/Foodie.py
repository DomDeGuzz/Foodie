from cgitb import handler
from email import message

import discord
from discord.ext import commands
import logging
from dotenv import load_dotenv
import os
from better_profanity import profanity
from recipe_storage import save_recipe, get_recipe, list_recipes
from recipe_scaler import parse_ingredient_string, scale_ingredients
from discord import app_commands

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

secret_role = "Foodie lover"
profanity_enabled = True
profanity.load_censor_words()

def normalize(name: str) -> str:
    return name.strip().lower()

@bot.event
async def on_ready():
    test_guild = discord.Object(id=1395311222643101727)

    await bot.tree.sync(guild=test_guild)
    print(f"✅ Slash commands synced to test guild: {test_guild.id}")

    await bot.tree.sync()
    print(f"🌍 Global slash commands synced.")

    print(f"Let's make some food, {bot.user.name}!")


@bot.event
async def on_member_join(member):
    await member.send(f"Welcome to the server {member.name}!")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if profanity_enabled and profanity.contains_profanity(message.content):
        await message.delete()
        await message.channel.send(f"{message.author.mention} don't use that word bruh.")
        return

    await bot.process_commands(message)

@bot.command(name="toggle_profanity")
@commands.has_permissions(administrator=True)  # Optional: restrict to admins
async def toggle_profanity(ctx):
    global profanity_enabled
    profanity_enabled = not profanity_enabled
    state = "enabled" if profanity_enabled else "disabled"
    await ctx.send(f"🧼 Profanity filter is now **{state}**.")

@bot.tree.command(name="toggle_profanity", description="Toggle the profanity filter (admin only)")
async def toggle_profanity_slash(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ You must be an administrator to use this.", ephemeral=True)
        return
    global profanity_enabled
    profanity_enabled = not profanity_enabled
    state = "enabled" if profanity_enabled else "disabled"
    await interaction.response.send_message(f"🧼 Profanity filter is now **{state}**.")

@bot.command()
async def hello(ctx):
    await ctx.send(f"Hello {ctx.author.mention}!")

@bot.tree.command(name="hello", description="Say hello to the bot")
async def hello_slash(interaction: discord.Interaction):
    await interaction.response.send_message(f"Hello {interaction.user.mention}!")

@bot.command()
async def assign(ctx):
    role = discord.utils.get(ctx.guild.roles, name=secret_role)
    if role:
        await ctx.author.add_roles(role)
        await ctx.send(f"{ctx.author.mention} You are now assigned to {secret_role}!")
    else:
        await ctx.send(f"Role doesn't exist!")

@bot.tree.command(name="assign", description="Assign yourself the 'Foodie lover' role")
async def assign_slash(interaction: discord.Interaction):
    role = discord.utils.get(interaction.guild.roles, name=secret_role)
    if role:
        await interaction.user.add_roles(role)
        await interaction.response.send_message(f"{interaction.user.mention} You are now assigned to {secret_role}!")
    else:
        await interaction.response.send_message("❌ Role doesn't exist.")

@bot.command()
async def dm_slash(interaction: discord.Interaction, message: str):
    await interaction.user.send(message)
    await interaction.response.send_message("📨 Message sent!", ephemeral=True)

@bot.tree.command(name="dm", description="Send yourself a private message")
@app_commands.describe(message="Message to send to yourself")
async def dm_slash(interaction: discord.Interaction, message: str):
    await interaction.user.send(message)
    await interaction.response.send_message("📨 Message sent!", ephemeral=True)

@bot.command()
async def reply_slash(interaction: discord.Interaction):
    await interaction.response.send_message("bruh moment")

@bot.tree.command(name="reply", description="Bot replies with 'bruh moment'")
async def reply_slash(interaction: discord.Interaction):
    await interaction.response.send_message("bruh moment")

@bot.command()
@commands.has_role(secret_role)
async def secret(ctx):
    await ctx.send(f"Welcome to the foodie club!")

@secret.error
async def secret_error(ctx, error):
    if isinstance(error, commands.MissingRole):
        await ctx.send("You don't have the required role to do that.")

@bot.command()
async def poll(ctx, *, question):
    embed = discord.Embed(title="Poll", description=question, color=discord.Color.green())
    poll_message = await ctx.send(embed=embed)
    await poll_message.add_reaction("👍")
    await poll_message.add_reaction("👎")

@bot.tree.command(name="poll", description="Create a 👍👎 poll")
@app_commands.describe(question="Poll question")
async def poll_slash(interaction: discord.Interaction, question: str):
    embed = discord.Embed(title="Poll", description=question, color=discord.Color.green())
    poll_msg = await interaction.channel.send(embed=embed)
    await poll_msg.add_reaction("👍")
    await poll_msg.add_reaction("👎")
    await interaction.response.send_message("✅ Poll created.", ephemeral=True)

from recipe_scaler import scale_ingredients

@bot.command()
async def scale(ctx, original: int, desired: int, *, ingredients_raw: str):

    try:
        parsed = parse_ingredient_string(ingredients_raw)
        if not parsed:
            await ctx.send("❌ Could not parse any ingredients.")
            return

        scaled = scale_ingredients(parsed, original, desired)

        lines = [f"📏 Scaled ingredients for {desired} servings:"]
        for ing in scaled:
            lines.append(f"- {ing['name']}: {ing['scaled_quantity']} {ing['unit']}")

        await ctx.send("\n".join(lines))
        await ctx.send("💾 Type `!save <name>` to save this recipe.")

        bot.last_scaled_recipe = {
            "ingredients": scaled,
            "servings": desired
        }

    except Exception as e:
        await ctx.send(f"❌ Error scaling recipe: {e}")

@bot.tree.command(name="scale", description="Scale a recipe")
@app_commands.describe(original="Original servings", desired="Desired servings", ingredients="Format: sugar:2tbsp, flour:3 cup")
async def scale_slash(interaction: discord.Interaction, original: int, desired: int, ingredients: str):
    parsed = parse_ingredient_string(ingredients)
    if not parsed:
        await interaction.response.send_message("❌ Could not parse any ingredients.", ephemeral=True)
        return

    scaled = scale_ingredients(parsed, original, desired)
    lines = [f"📏 Scaled ingredients for {desired} servings:"]
    for ing in scaled:
        lines.append(f"- {ing['name']}: {ing['scaled_quantity']} {ing['unit']}")

    bot.last_scaled_recipe = {
        "ingredients": scaled,
        "servings": desired
    }

    await interaction.response.send_message(
        "\n".join(lines) + "\n💾 Type `/save <name>` to save this recipe."
    )


    bot.last_scaled_recipe = {
        "ingredients": scaled,
        "servings": desired
    }

@bot.command()
async def save(ctx, name: str):
    if not hasattr(bot, "last_scaled_recipe"):
        await ctx.send("❌ No recipe to save. Use `!scale` first.")
        return
    save_recipe(normalize(name), bot.last_scaled_recipe["ingredients"], bot.last_scaled_recipe["servings"])
    await ctx.send(f"✅ Saved recipe as `{name}`.")

@bot.tree.command(name="save", description="Save the last scaled recipe")
@app_commands.describe(name="Recipe name to save")
async def save_slash(interaction: discord.Interaction, name: str):
    if not hasattr(bot, "last_scaled_recipe"):
        await interaction.response.send_message("❌ No recipe to save. Use `/scale` first.", ephemeral=True)
        return
    save_recipe(normalize(name), bot.last_scaled_recipe["ingredients"], bot.last_scaled_recipe["servings"])
    await interaction.response.send_message(f"✅ Saved recipe as `{name}`.")

@bot.command()
async def recipe(ctx, name: str):
    recipe = get_recipe(normalize(name))
    if not recipe:
        await ctx.send("❌ Recipe not found.")
        return

    lines = [f"📖 **{name.title()}** ({recipe['servings']} servings)"]
    for ing in recipe["ingredients"]:
        lines.append(f"- {ing['name']}: {ing['scaled_quantity']} {ing['unit']}")
    await ctx.send("\n".join(lines))

@bot.tree.command(name="recipe", description="Get a saved recipe by name")
@app_commands.describe(name="Recipe name to retrieve")
async def recipe_slash(interaction: discord.Interaction, name: str):
    recipe = get_recipe(normalize(name))
    if not recipe:
        await interaction.response.send_message("❌ Recipe not found.")
        return

    lines = [f"📖 **{name.title()}** ({recipe['servings']} servings)"]
    for ing in recipe["ingredients"]:
        lines.append(f"- {ing['name']}: {ing['scaled_quantity']} {ing['unit']}")
    await interaction.response.send_message("\n".join(lines))

@bot.command()
async def recipes(ctx):
    names = list_recipes()
    if not names:
        await ctx.send("📭 No saved recipes.")
    else:
        await ctx.send("📚 Saved recipes:\n" + "\n".join(f"- {n}" for n in names))

@bot.tree.command(name="recipes", description="List all saved recipes")
async def recipes_slash(interaction: discord.Interaction):
    names = list_recipes()
    if not names:
        await interaction.response.send_message("📭 No saved recipes.")
    else:
        await interaction.response.send_message("📚 Saved recipes:\n" + "\n".join(f"- {n}" for n in names))

@bot.command(name="recipe_add_ingredient")
async def recipe_add_ingredient(ctx, recipe_name: str, ingredient_name: str, quantity: float, unit: str):
    recipe = get_recipe(normalize(recipe_name))
    if not recipe:
        await ctx.send(f"❌ Recipe `{recipe_name}` not found.")
        return

    new_ingredient = {
        "name": ingredient_name,
        "quantity": quantity,
        "unit": unit,
        "scaled_quantity": quantity
    }

    recipe["ingredients"].append(new_ingredient)
    save_recipe(recipe_name, recipe["ingredients"], recipe["servings"])

    await ctx.send(f"✅ Added `{ingredient_name}` ({quantity} {unit}) to `{recipe_name}`.")

@bot.tree.command(name="recipe_add_ingredient", description="Add an ingredient to a saved recipe")
@app_commands.describe(recipe_name="Name of the recipe", ingredient_name="Ingredient name", quantity="Amount", unit="Unit (e.g., cup)")
async def recipe_add_slash(interaction: discord.Interaction, recipe_name: str, ingredient_name: str, quantity: float, unit: str):
    recipe = get_recipe(normalize(recipe_name))
    if not recipe:
        await interaction.response.send_message(f"❌ Recipe `{recipe_name}` not found.")
        return

    new_ingredient = {
        "name": ingredient_name,
        "quantity": quantity,
        "unit": unit,
        "scaled_quantity": quantity
    }

    recipe["ingredients"].append(new_ingredient)
    save_recipe(recipe_name, recipe["ingredients"], recipe["servings"])

    await interaction.response.send_message(f"✅ Added `{ingredient_name}` ({quantity} {unit}) to `{recipe_name}`.")

@bot.command(name="recipe_remove_ingredient")
async def recipe_remove_ingredient(ctx, recipe_name: str, ingredient_name: str):
    recipe = get_recipe(normalize(recipe_name))
    if not recipe:
        await ctx.send(f"❌ Recipe `{recipe_name}` not found.")
        return

    before = len(recipe["ingredients"])
    recipe["ingredients"] = [
        ing for ing in recipe["ingredients"]
        if normalize(ing["name"]) == normalize(ingredient_name)
    ]
    after = len(recipe["ingredients"])

    if before == after:
        await ctx.send(f"❌ `{ingredient_name}` not found in `{recipe_name}`.")
    else:
        save_recipe(recipe_name, recipe["ingredients"], recipe["servings"])
        await ctx.send(f"🗑️ Removed `{ingredient_name}` from `{recipe_name}`.")

@bot.tree.command(name="recipe_remove_ingredient", description="Remove an ingredient from a saved recipe")
@app_commands.describe(recipe_name="Name of the recipe", ingredient_name="Ingredient to remove")
async def recipe_remove_slash(interaction: discord.Interaction, recipe_name: str, ingredient_name: str):
    recipe = get_recipe(normalize(recipe_name))
    if not recipe:
        await interaction.response.send_message(f"❌ Recipe `{recipe_name}` not found.")
        return

    before = len(recipe["ingredients"])
    recipe["ingredients"] = [
        ing for ing in recipe["ingredients"]
        if normalize(ing["name"]) == normalize(ingredient_name)
    ]
    after = len(recipe["ingredients"])

    if before == after:
        await interaction.response.send_message(f"❌ `{ingredient_name}` not found in `{recipe_name}`.")
    else:
        save_recipe(recipe_name, recipe["ingredients"], recipe["servings"])
        await interaction.response.send_message(f"🗑️ Removed `{ingredient_name}` from `{recipe_name}`.")

@bot.command(name="edit_ingredient")
async def edit_ingredient(ctx, recipe_name: str, ingredient_name: str, new_quantity: float, new_unit: str):
    recipe = get_recipe(normalize(recipe_name))
    if not recipe:
        await ctx.send(f"❌ Recipe `{recipe_name}` not found.")
        return

    found = False
    for ing in recipe["ingredients"]:
        if normalize(ing["name"]) == normalize(ingredient_name):
            ing["quantity"] = new_quantity
            ing["scaled_quantity"] = new_quantity
            ing["unit"] = new_unit
            found = True
            break

    if not found:
        await ctx.send(f"❌ Ingredient `{ingredient_name}` not found in `{recipe_name}`.")
        return

    save_recipe(recipe_name, recipe["ingredients"], recipe["servings"])
    await ctx.send(f"✏️ Updated `{ingredient_name}` in `{recipe_name}` to {new_quantity} {new_unit}.")

from recipe_storage import delete_recipe

@bot.tree.command(name="edit_ingredient", description="Edit an ingredient in a saved recipe")
@app_commands.describe(recipe_name="Recipe name", ingredient_name="Ingredient to edit", new_quantity="New quantity", new_unit="New unit")
async def edit_ingredient_slash(interaction: discord.Interaction, recipe_name: str, ingredient_name: str, new_quantity: float, new_unit: str):
    recipe = get_recipe(normalize(recipe_name))
    if not recipe:
        await interaction.response.send_message(f"❌ Recipe `{recipe_name}` not found.")
        return

    found = False
    for ing in recipe["ingredients"]:
        if normalize(ing["name"]) == normalize(ingredient_name):
            ing["quantity"] = new_quantity
            ing["scaled_quantity"] = new_quantity
            ing["unit"] = new_unit
            found = True
            break

    if not found:
        await interaction.response.send_message(f"❌ Ingredient `{ingredient_name}` not found in `{recipe_name}`.")
        return

    save_recipe(recipe_name, recipe["ingredients"], recipe["servings"])
    await interaction.response.send_message(f"✏️ Updated `{ingredient_name}` in `{recipe_name}` to {new_quantity} {new_unit}.")


@bot.command(name="delete_recipe")
async def delete_recipe_cmd(ctx, name: str):
    success = delete_recipe(normalize(name))
    if success:
        await ctx.send(f"🗑️ Deleted recipe `{name}`.")
    else:
        await ctx.send(f"❌ Could not find recipe `{name}`.")

@bot.tree.command(name="delete_recipe", description="Delete a saved recipe")
@app_commands.describe(name="Recipe name to delete")
async def delete_recipe_slash(interaction: discord.Interaction, name: str):
    from recipe_storage import delete_recipe

    success = delete_recipe(normalize(name))
    if success:
        await interaction.response.send_message(f"🗑️ Deleted recipe `{name}`.")
    else:
        await interaction.response.send_message(f"❌ Could not find recipe `{name}`.")

@bot.command(name="sync")
@commands.is_owner()
async def sync_commands(ctx):
    guild = ctx.guild
    await bot.tree.sync(guild=guild)
    await ctx.send(f"✅ Slash commands synced to guild `{guild.name}` ({guild.id}).")


@bot.command(name="help")
async def help_command(ctx):
    help_text = """
🤖 **Available Commands**

🔧 **General**
`!hello` — Say hello to the bot  
`!help` — Show this help message  
`!assign` — Assign yourself the 'Foodie lover' role  
`!secret` — Secret club command (requires role)

📬 **Messaging**
`!dm <message>` — Send yourself a private message  
`!reply` — Bot replies with 'bruh moment'  
`!poll <question>` — Create a 👍👎 reaction poll

📐 **Recipe Scaling**
`!scale <original> <desired> <ingredients>` — Scale ingredients  
Example: `!scale 2 4 sugar:2 tbsp, flour:3 cup`

💾 **Recipe Saving & Retrieval**
`!save <name>` — Save the most recent scaled recipe  
`!recipes` — List all saved recipes  
`!recipe <name>` — View a saved recipe
`!delete_recipe <name>` — 🗑️ Delete a saved recipe

🧪 **Edit Saved Recipes**
`!recipe_add_ingredient <recipe> <name> <qty> <unit>` — Add to a saved recipe  
`!recipe_remove_ingredient <recipe> <name>` — Remove from a saved recipe  
`!edit_ingredient <recipe> <name> <new_qty> <new_unit>` — Edit an ingredient in a saved recipe

🧼 **Profanity Filter**
Bad words are automatically deleted from chat.  
Use `!toggle_profanity` to turn the filter on or off (admin only).
"""


    await ctx.send(help_text)

@bot.tree.command(name="help", description="List all commands")
async def help_slash(interaction: discord.Interaction):
    help_text = """
🤖 **Available Commands**

🔧 **General**
`!hello`, `/hello` — Say hello  
`!help`, `/help` — Show this help message  
`!assign`, `/assign` — Assign yourself the 'Foodie lover' role  
`!secret` — Secret club command (requires role)

📬 **Messaging**
`!dm`, `/dm` — DM yourself  
`!reply`, `/reply` — Funny reply  
`!poll`, `/poll` — Start a poll

📐 **Scaling Recipes**
`!scale`, `/scale` — Scale ingredients

💾 **Manage Recipes**
`!save`, `/save` — Save recipe  
`!recipe`, `/recipe` — View recipe  
`!recipes`, `/recipes` — List recipes  
`!delete_recipe`, `/delete_recipe` — 🗑️ Delete recipe

🧪 **Edit Recipes**
`!recipe_add_ingredient`, `/recipe_add_ingredient` — Add ingredient  
`!recipe_remove_ingredient`, `/recipe_remove_ingredient` — Remove ingredient  
`!edit_ingredient`, `/edit_ingredient` — Edit ingredient

🧼 **Profanity Filter**
`!toggle_profanity`, `/toggle_profanity` — Toggle profanity filter (admin)
"""
    await interaction.response.send_message(help_text, ephemeral=True)

bot.run(TOKEN, log_handler=handler, log_level=logging.DEBUG)

