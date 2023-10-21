#import pyray as ray
import os
import json
from enum import Enum
import random
import copy
from threading import Thread

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
  def __init__(self, objects):
    self.pokedex = objects
    self.player = [{"pokemon": {}}, {"pokemon": {}}]
    self.player[0]["pokemon"] = []
    self.player[1]["pokemon"] = []
  def push_pokemon(self, player_id, pokemon_data):
    self.player[player_id]["pokemon"].append(pokemon_data)
  def remove_pokemon(self, player_id, pokemon_id):
    for index, pokemon in enumerate(self.player[player_id]["pokemon"]):
      if pokemon["id"] == pokemon_id:
        del self.player[player_id]["pokemon"][index]
  def get_pokemon_by_id(self, pokemon_id):
    for index, pokemon in enumerate(self.pokedex):
      if pokemon["id"] == pokemon_id:
        return pokemon
  def get_pokemon_by_name(self, pokemon_name):
    for index, pokemon in enumerate(self.pokedex):
        current_name = str(pokemon["name"]["english"]).lower()
        pokemon_name = str(pokemon_name).lower()
        if current_name == pokemon_name:
          return pokemon
        
  def simulate_battle(self):
    player_a = self.player[0]
    player_b = self.player[1]
    pokemons = [player_a["pokemon"], player_b["pokemon"]]

    hps = []
    hps.append(pokemons[0][0]['base']['HP'])
    hps.append(pokemons[1][0]['base']['HP'])

    turn = 0
    while len(pokemons[0]) > 0 and len(pokemons[1]) > 0:
      print(f"Currently battling pokemon: {pokemons[0][0]['name']['english']} and {pokemons[1][0]['name']['english']}")
      while hps[0] > 0 and hps[1] > 0:
        pokemon_to_attack = pokemons[0][0] if turn == 0 else pokemons[1][0]
        pokemon_to_be_attacked = pokemons[1][0] if turn == 0 else pokemons[0][0]
        
        current_damage = calculate_damage(pokemon_to_attack, pokemon_to_be_attacked)
        print(f"{pokemon_to_attack['name']['english']} caused {current_damage} to {pokemon_to_be_attacked['name']['english']}")
        turn = 0 if turn == 1 else 1
        hps[turn] -= current_damage
      for i in range(0,2):
        if hps[i] < 0:
          print(f"{pokemons[i][0]['name']['english']} was defeated!")
          del pokemons[i][0]
          if len(pokemons[i]) > 0:
            hps[i] = pokemons[i][0]['base']['HP']
    for i in range(0,2):
      if len(pokemons[i]) > 0:
        print(f"Trainer {i} won!")
        
'''
def load_textures(objects):
  for o in objects:
    o["back_texture"] = ray.load_texture(o["sprites"]["back"])
    o["front_texture"] = ray.load_texture(o["sprites"]["front"])
    if o["back_texture"].width == 0 or o["front_texture"].width == 0:
      raise RuntimeError("Texture could not be loaded")
'''
      
def load_objects(result):
  with open('pokedex.json', 'r') as f:
    objects = json.loads(f.read())
  sprite_list = os.listdir('sprites')
  #print(f"sprite list: {sprite_list}")
  #load_textures(objects)
  if len(objects) > 0:
    result = True
  return objects

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

'''
def draw_loading_screen():
  ray.draw_text("LOADING...", int(1280 / 2) - 40, int(720 / 2) - 40, 40, ray.BLACK)

def draw_game(objects):
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
'''
      
# The default pokemon for now will be: charmander, bulbasaur and squirtle, for both players.

objects_loaded = False

#ray.init_window(1280, 720, "PokeRedes")
#ray.set_target_fps(60)

objects = load_objects(objects_loaded)

game_state = GameState(objects)
game_state.push_pokemon(0, game_state.get_pokemon_by_name("bulbasaur"))
game_state.push_pokemon(0, game_state.get_pokemon_by_name("charmander"))
game_state.push_pokemon(0, game_state.get_pokemon_by_name("squirtle"))

game_state.push_pokemon(1, game_state.get_pokemon_by_name("squirtle"))
game_state.push_pokemon(1, game_state.get_pokemon_by_name("bulbasaur"))
game_state.push_pokemon(1, game_state.get_pokemon_by_name("charmander"))

battle_thread = Thread(target=game_state.simulate_battle)
#game_state.simulate_battle()
battle_thread.start()

#print(f"objects: {objects}")

'''
while not ray.window_should_close():
  ray.begin_drawing()
  ray.clear_background(ray.RAYWHITE)

  draw_game(objects)
  

  ray.draw_fps(ray.get_render_width() - 30, 10) 
  ray.end_drawing()
'''