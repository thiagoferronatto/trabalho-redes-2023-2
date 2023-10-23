
import os
import sys
#sys.path.insert(0, 'pyray')
#import pyray as rl
import json
import random
from threading import Thread
import socket

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
    self.pokedex = self.load_objects()
    num_jogadores  = 2
    self.player = [{"pokemon": [], "hp_data": [], "name": str} for _ in range(num_jogadores)]
  
  def load_objects(self):
    with open('pokedex.json', 'r') as f:
      objects = json.loads(f.read())
    # TODO: Load sprites?
    return objects
  
  def print_poke(self, poke):
    print(f"Pokemon ID: {poke['id']}")
    print(f"Pokemon name: {poke['name']['english']}")
    print(f"Pokemon stats:")
    for stat, value in poke['base'].items():
      print(f"\t{stat}: {value}")
    print("Types:")
    for type in poke['type']:
      print(f"\t{type}")
    print("==========================================")

  def print_party(self, party):
    for poke in party:
      self.print_poke(poke)
  
  def set_hp_data(self, player_id):
    """
    Capta os Health Points de uma party e os salva numa lista separada, para calcular mais fácil as batalhas
    Args:
      party: lista de Pokémon
    """
    for poke in self.player[player_id]["pokemon"]:
      self.player[player_id]["hp_data"].append(poke["base"]["HP"])
  
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
    
    if len(player_a) == 0 or len(player_b) == 0:
      print(f"One of the parties is empty! :(")
      return
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
        
        current_damage = self.calculate_damage(pokemon_to_attack, pokemon_to_be_attacked)
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
  
  # Função para adicionar um Pokémon individual (ETAPA 1)
  def add_individual_pokemon(self):
    print("Digite o id ou nome do Pokémon:")
    pokemon_id = input()
    # Implemente a lógica para adicionar o Pokémon
    if pokemon_id.isdigit():
      pokemon = self.get_pokemon_by_id(int(pokemon_id))
    elif pokemon_id == None:
      print(f'Digite o um valor válido!')
      return 1
    else:
      pokemon = self.get_pokemon_by_name(pokemon_id)
    
    print(f"O Pokémon que você escolheu é {pokemon}, confirma? [s/n]")
    resposta = input()
    if resposta.lower() == "s":
      self.push_pokemon(0, pokemon)
      return 0  # Retorna à etapa 0
    else:
      return 1  # Volta à etapa 1

  def translate_party_to_pokemon_data(self, party):
    result = []
    for p in party:
      result.append(self.get_pokemon_by_id(int(p)))
    return result

  def add_party_to_player(self, party, player_id) -> bool:
    """
    Adiciona uma lista de pokemons ao jogador do id determinado. ID 0 = jogador, ID 1 = adversário
    Args:
      party: lista de pokemon
      player_id: id do player
    Returns:
      True se a operação funcionou, False caso não tenha funcionado
    """
    print(party)
    
    current_player = self.player[player_id]
    if len(current_player.get("pokemon")) == 0:
      current_player["pokemon"] = party
      self.set_hp_data(player_id)
      if player_id == 0:
        print("Your party is:")
      else:
        print("Your opponent party is:")
      for poke in party:
        print(f"- {poke['name']['english']}")
      return True
    else:
      return False

  # Função para adicionar uma party inteira (ETAPA 2)
  def adicionar_party(self):
    print("Digite os ids dos 6 Pokémon:")
    ids_pokemons = input().split()
    
    todos_sao_digitos = all(item.isdigit() for item in ids_pokemons)
    
    if len(ids_pokemons) != 6 or not todos_sao_digitos:
      return 2
    
    party = self.translate_party_to_pokemon_data(ids_pokemons)
    print(f"Os Pokémon que você selecionou são:")
    self.print_party(party)
    
    #pprint(party)
    print(f"Deseja refazer? [s/n]")
    resposta = input()
    if resposta.lower() == "s":
      return 2  # Retorna à etapa 2
    else:
      self.player[0]['pokemon'] = party
      self.set_hp_data(0)
      return 0  # Volta à etapa 0

  def calculate_type_effectiveness(self, pokemon_a_types, pokemon_b_types):
    result = 1.0
    # aqui checamos em cada entrada do dicionário para verificar os multiplicadores de tipo
    for ef_a in pokemon_a_types:
      for ef_b in pokemon_b_types:
        result *= type_effectiveness[ef_a].get(ef_b, 1.0) # caso não haja nenhuma entrada no dicionário para o tipo atual, multiplicamos por 1.0

    if result > 1.0:
      print("Attack was super effective!")
    return result

  # Aqui calculamos o dano aplicado de um pokemon ao outro, de acordo com a fórmula descrita em https://bulbapedia.bulbagarden.net/wiki/Damage
  def calculate_damage(self, pokemon_a, pokemon_b):
    modifier = random.uniform(0.01, 1.00)
    critical = 2 if modifier > 0.15 else 1 # se o numero aleatório for menor que 0.15, o dano crítico será aplicado (15% de chance)
    effectiveness = self.calculate_type_effectiveness(pokemon_a['type'], pokemon_b['type']) # calculando o multiplicador de efetividade de tipos
    randomness = random.uniform(0.85, 1.0)
    upper_part = (((((2 * 40 * critical) / 5) + 2) * 40 * (pokemon_a['base']['Attack'] / pokemon_b['base']['Defense'])) / 50) + 2
    outer_part = (effectiveness * randomness)
    damage = upper_part * outer_part
    return damage


  # Função para listar todos os Pokémon (ETAPA 3)
  def listar_pokemon(self):
    for o in self.pokedex:
      print(f"{o['id']} - {o['name']['english']}")
    return 0  # Volta à etapa 0

  # Função para consultar dados de um Pokémon específico (ETAPA 4)
  def consultar_pokemon(self):
    print("Digite o id ou nome do Pokémon:")
    id_ou_nome = input()
    pokemon_data = None
    if id_ou_nome.isdigit():
      pokemon_data = self.get_pokemon_by_id(int(id_ou_nome))
    else:
      pokemon_data = self.get_pokemon_by_name(id_ou_nome)
    self.print_poke(pokemon_data)
    return 0  # Volta à etapa 0

  # Função principal
  def menu(self):
    etapa = 0  # Inicia na etapa 0

    previous_party_size = 0
    party_full = False
    while True:
      current_party_size = len(self.player[0]['pokemon'])
      if current_party_size != previous_party_size:
        print(f"Sua party é a seguinte: ")
        self.print_party(self.player[0]["pokemon"])
        previous_party_size = current_party_size
        
      if current_party_size == 6 and not party_full:
        print(f"Os 6 pokemons foram adicionados!")
        party_full = True
      
      if etapa == 0:
        if not party_full:
          print("1 - Adicionar Pokémon individual")
          print("2 - Adicionar party inteira")
        print("3 - Consultar Pokémon")
        print("4 - Consultar dados de Pokémon específico")
        print("5 - Confirmar party e procurar jogo")
        opcao = input("Selecione uma opção: ")

        # TODO: O código está duplicado. Poderia ser mais bonito, mas por enquanto funciona hehe

        if opcao == "1" and not party_full:
          etapa = self.add_individual_pokemon()
        elif opcao == "2" and not party_full:
          etapa = self.adicionar_party()
        elif opcao == "3":
          etapa = self.listar_pokemon()
        elif opcao == "4":
          etapa = self.consultar_pokemon()
        elif opcao == "5":
           etapa = 5

      elif etapa == 1:
          etapa = self.add_individual_pokemon()

      elif etapa == 2:
          etapa = self.adicionar_party()

      elif etapa == 3:
          etapa = self.listar_pokemon()

      elif etapa == 4:
          etapa = self.consultar_pokemon()
      elif etapa == 5:
        if len(self.player[0]["pokemon"]) == 0:
          print("É necessário escolher pelo menos um pokémon!")
          etapa = 0
        else:
          break

  def get_ids_from_party(self, party):
    ids = []
    for poke in party:
      ids.append(poke["id"])
    return ids
  
  def encode_id_list_into_string(self, list):
    result = ""
    for id_ in list:
      result += f"{id_} "
    return result




# The default pokemon for now will be: charmander, bulbasaur and squirtle, for both players.

'''
objects_loaded = False

# NOTE(yuri): O raylib só funciona com python 3.11 e versões inferiores. Tentei rodar ele de todas as formas
# com o python 3.12, mas infelizmente a unica solução é instalar alguns arquivos manualmente, o que creio que
# não seja uma boa ideia, portanto o jogo só vai poder ser executado pelas versões 3.11 pra baixo.
#rl.init_window(1280, 720, "seloco")
#rl.set_target_fps(60)

objects = load_objects(objects_loaded)

game_state = GameState(objects)

print(f"Bem-vindo ao PokéRedes!")
print(f"Crie sua party, ela deve ter no mínimo 1 pokémon e no máximo 6!")
# Inicie o menu
menu(game_state)

# ALERTA: O segundo jogador, por enquanto, será um jogador com party hipotética, a partir do momento que implementarmos os sockets, a party será transmitida pelo adversário
# até a porta que o jogador cliente estará ouvindo. Após as partys estiverem bem definidas, o jogo começará.

game_state.push_pokemon(1, game_state.get_pokemon_by_name("dragonite"))
game_state.push_pokemon(1, game_state.get_pokemon_by_name("mew"))
game_state.push_pokemon(1, game_state.get_pokemon_by_name("mewtwo"))

battle_thread = Thread(target=game_state.simulate_battle)
battle_thread.start()

def listen_to_player():
  PORTA_HIPOTETICA = 12345
  HOST_HIPOTETICO = 'localhost'  
  sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  sock.listen()
  sock.recv()

# TODO: listening thread only for testing purposes
listening_thread = Thread(target=listen_to_player)
#listening_thread = 

'''

'''
while not rl.window_should_close():
  rl.begin_drawing()
  rl.clear_background(rl.RAYWHITE)
  x = 0
  y = 30
  for o in objects:
    rl.draw_text(str(o['id']), x+32,y-20,30, rl.RED)
    rl.draw_rectangle_lines(x, y, 64, 64, rl.RED)
    rl.draw_texture_pro(o["back_texture"], (0, 0, o["back_texture"].width, o["back_texture"].height), (x, y, 64, 64), (0, 0), 0, rl.WHITE)
    
    x += 64
    if x > 1280:
      y += 64
      x = 0
    rl.draw_fps(5, 5)
  
  rl.end_drawing()
# END LOOP
rl.close_window()
'''
