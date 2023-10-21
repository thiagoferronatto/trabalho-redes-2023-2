import pyray as ray
import os
import json
from enum import Enum
import random
import copy

type_effectiveness = {
  "Normal": {"Rock": 0.5, "Ghost": 0, "Steel": 0.5},
  "Fire": {"Fire": 0.5, "Water": 0.5, "Grass": 2, "Ice": 2, "Bug": 2, "Rock": 0.5, "Dragon": 0.5, "Steel": 2},
  "Water": {"Fire": 2, "Water": 0.5, "Grass": 0.5, "Poison": 0.5, "Ground": 2, "Rock": 2, "Dragon": 0.5},
  "Electric": {"Water": 2, "Electric": 0.5, "Grass": 0.5, "Ground": 0, "Flying": 2, "Dragon": 0.5},
  "Grass": {"Fire": 0.5, "Water": 2, "Grass": 0.5, "Poison": 0.5, "Flying": 0.5, "Bug": 0.5, "Rock": 2, "Dragon": 0.5, "Steel": 0.5},
  "Ice": {"Fire": 0.5, "Water": 0.5, "Grass": 2, "Ice": 0.5, "Ground": 2, "Flying": 2, "Dragon": 2, "Steel": 0.5},
  "Fighting": {"Normal": 2, "Ice": 2, "Poison": 0.5, "Flying": 0.5, "Psychic": 0.5, "Bug": 0.5, "Rock": 2, "Ghost": 0, "Dark": 2, "Steel": 2, "Fairy": 0.5},
  "Poison": {"Grass": 2, "Poison": 0.5, "Ground": 0.5, "Rock": 0.5, "Ghost": 0.5, "Steel": 0, "Fairy": 0.5},
  "Ground": {"Fire": 2, "Electric": 2, "Grass": 0.5, "Poison": 2, "Flying": 0, "Bug": 0.5, "Rock": 2, "Steel": 2},
  "Flying": {"Electric": 0.5, "Grass": 2, "Fighting": 2, "Bug": 2, "Rock": 0.5, "Steel": 0.5},
  "Psychic": {"Fighting": 2, "Poison": 2, "Dark": 0, "Steel": 0.5},
  "Bug": {"Fire": 0.5, "Grass": 2, "Fighting": 0.5, "Poison": 0.5, "Flying": 0.5, "Psychic": 2, "Ghost": 0.5, "Dark": 2, "Steel": 0.5, "Fairy": 0.5},
  "Rock": {"Fire": 2, "Ice": 2, "Fighting": 0.5, "Ground": 0.5, "Flying": 2, "Bug": 2, "Steel": 0.5},
  "Ghost": {"Normal": 0, "Psychic": 2, "Ghost": 2, "Dark": 0.5},
  "Dragon": {"Dragon": 2, "Steel": 0.5, "Fairy": 0.5},
  "Dark": {"Poison": 0.5, "Psychic": 2, "Ghost": 2, "Dark": 0.5, "Fairy": 0.5},
  "Steel": {"Fire": 0.5, "Water": 0.5, "Electric": 0.5, "Ice": 2, "Rock": 2, "Steel": 0.5, "Fairy": 2},
  "Fairy": {"Fire": 0.5, "Ice": 2, "Fighting": 0.5, "Dragon": 2, "Dark": 2, "Steel": 0.5},
}

class GameState():
  def __init__(self):
    self.player = [{"pokemon": {}}, {"pokemon": {}}]
    self.player[0]["pokemon"] = []
    self.player[1]["pokemon"] = []
  def push_pokemon(self, player_id, pokemon_data):
    self.player[player_id].push(pokemon_data)

class PokemonTypes(Enum):
  FIRE = 1
  WATER = 2
  GRASS = 3

def load_objects():
  with open('pokedex.json', 'r') as f:
    objects = json.loads(f.read())
  sprite_list = os.listdir('sprites')
  #print(f"sprite list: {sprite_list}")
  for o in objects:
    o["back_texture"] = ray.load_texture(o["sprites"]["back"])
    o["front_texture"] = ray.load_texture(o["sprites"]["front"])
    if o["back_texture"].width == 0 or o["front_texture"].width == 0:
      raise RuntimeError("Texture could not be loaded")
  return objects

def load_pokedex():
  with open('new_pokedex.json', 'r', encoding="utf8") as f:
    objects = json.loads(f.read())
  print(f"{objects}")

def calculate_type_effectiveness(pokemon_a_types, pokemon_b_types):
  result = 1.0
  # aqui checamos em cada entrada do dicionário para verificar os multiplicadores de tipo
  for ef_a in pokemon_a_types:
    for ef_b in pokemon_b_types:
      result *= type_effectiveness[ef_a].get(ef_b, 1.0) # caso não haja nenhuma entrada no dicionário para o tipo atual, multiplicamos por 1.0

  if result > 1.0:
    print("Attack was super effective!")
  return result

def calculate_damage(pokemon_a, pokemon_b):
  modifier = random.uniform(0.01, 1.00)
  critical = 2 if modifier > 0.15 else 1 # se o numero aleatório for menor que 0.15, o dano crítico será aplicado (15% de chance)
  level = 30 # level sempre será 30, por motivos de: não achei um jeito interessante de calular os levels :(
  effectiveness = calculate_type_effectiveness(pokemon_a['type'], pokemon_b['type']) # calculando o multiplicador de efetividade de tipos
  randomness = random.uniform(0.85, 1.0)
  upper_part = (((((2 * 40 * critical) / 5) + 2) * 40 * (pokemon_a['base']['Attack'] / pokemon_b['base']['Defense'])) / 50) + 2
  outer_part = (effectiveness * randomness)
  damage = upper_part * outer_part
  return damage

def simulate_battle(pokemons_to_simulate):
  pokemon_a = pokemons_to_simulate[0]
  pokemon_b = pokemons_to_simulate[1]
  hps = [pokemon_a['base']['HP'], pokemon_b['base']['HP']]

  turn = 0
  while hps[0] > 0 and hps[1] > 0:
    pokemon_to_attack = pokemon_a if turn == 0 else pokemon_b
    pokemon_to_be_attacked = pokemon_b if turn == 0 else pokemon_a
    
    current_damage = calculate_damage(pokemon_to_attack, pokemon_to_be_attacked)
    print(f"{pokemon_to_attack['name']} caused {current_damage} to {pokemon_to_be_attacked['name']}")
    hps[turn] -= current_damage
    turn = 0 if turn == 1 else 1
  for i in range(0,1):
    if hps[i] < 0:
      print(f"{pokemons_to_simulate[i]['name']} won!")

# The default pokemon for now will be: charmander, bulbasaur and squirtle, for both players.
game_state = GameState()

ray.init_window(1280, 720, "PokeRedes")
ray.set_target_fps(60)

try:
  objects = load_objects()
except RuntimeError as e:
 print(f"{e}")
 exit(1)

pokemon_a_value = random.randint(1, 151)
pokemon_b_value = random.randint(1, 151)

pokemon_a = {
  'name': objects[pokemon_a_value]['name']['english'],
  'type': objects[pokemon_a_value]['type'],
  'base': objects[pokemon_a_value]['base']
}
pokemon_b = {
  'name': objects[pokemon_b_value]['name']['english'],
  'type': objects[pokemon_b_value]['type'],
  'base': objects[pokemon_b_value]['base']
}
pokemons_to_simulate = [pokemon_a, pokemon_b]
simulate_battle(pokemons_to_simulate)

print(f"Pokemon A: {pokemons_to_simulate[0]}")
print(f"Pokemon B: {pokemons_to_simulate[1]}")

#print(f"objects: {objects}")

while not ray.window_should_close():
  ray.begin_drawing()
  ray.clear_background(ray.RAYWHITE)

  x = 0
  y = 30
  for o in objects:
    ray.draw_text(str(o["id"]), x + 32, y - 20, 30, ray.RED)
    ray.draw_rectangle_lines(x, y, 64, 64, ray.RED)
    #ray.draw_texture(o["back_texture"], x, y, ray.WHITE)
    ray.draw_texture_pro(o["back_texture"], (0, 0, o["back_texture"].width, o["back_texture"].height), (x, y, 64, 64), (0, 0), 0, ray.WHITE)
    x += 64
    if x > 1280:
      y += 64
      x = 0

  ray.draw_fps(ray.get_render_width() - 30, 10) 
  ray.end_drawing()