"""
game.py

Autores: Thiago Ferronatto and Yuri Moraes Gavilan

Esse arquivo contem a classe GameState e o dicionário type_effectiveness para um jogo de Pokémon.

A classe GameState representa o estado de um jogo Pokémon, incuindo a Pokédex,
os jogadores, e suas equipes. Também oferece métodos para adição, consulta, remoção, entre outras operações
necessárias para a execução de uma partida.

"""


import json
import random




"""
Essa variável type_effectiveness é um dicionário que representa se um Pokémon possui um tipo que domina
o Pokémon pertencente a outro tipo; por exemplo: um Pokémon de fogo irá aplicar duas vezes mais dano em Pokémon de tipo grama, gelo, inseto, etc.
Assim como alguns Pokémon também são completamente imúnes a outros. Exemplo: um Pokémon fantasma é imune a um Pokémon do tipo lutador.
Esse dicionário será consultado pelo método GameState::calculate_damage(), onde um multiplicador será gerado a partir da combinação de todos os tipos
de um Pokémon A com outro Pokémon B (afinal, um Pokémon pode ter mais de um tipo).
"""

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
    # A Pokédex é a base de dados com todos os Pokémon
    self.pokedex = self.load_objects()
    
    # Aqui iniciamos uma lista de jogadores (nesse caso, dois).
    num_jogadores  = 2
    self.player = [{"pokemon": [], "hp_data": [], "name": str} for _ in range(num_jogadores)]
  
  def load_objects(self):
    """
    Carrega a base de dados do arquivo pokedex.json
    Returns:
      Lista de todos os Pokémon do arquivo pokedex.json
    """
    # 
    with open('../data/pokedex.json', 'r') as f:
      objects = json.loads(f.read())
    return objects
  
  def print_poke(self, poke):
    """
    Imprime os dados detalhados de um Pokémon.
    Args:
      poke: dado de um Pokémon assim como ele é lido da Pokédex.
    """
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
    """
    Imprime os dados detalhados de todos os Pokémon de um time.
    Args:
      party: lista de dados de Pokémon.
    """
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
    """
    Adiciona um Pokémon específico ao time de um jogador.
    Args:
      player_id: ID do jogador que terá o Pokémon adicionado ao seu time.
      pokemon_data: Dados do Pokémon que será adicionado ao time do jogador.
    """
    self.player[player_id]["pokemon"].append(pokemon_data)
    self.player[player_id]["hp_data"].append(pokemon_data["base"]["HP"])
  
  def remove_pokemon(self, player_id, pokemon_id):
    """
    Remove um Pokémon específico do time de um jogador (caso ele faça parte).
    Args:
      player_id: ID do jogador que terá o Pokémon removido do seu time.
      pokemon_id: ID do Pokémon que será removido do time do jogador.
    """
    for index, pokemon in enumerate(self.player[player_id]["pokemon"]):
      if pokemon["id"] == pokemon_id:
        del self.player[player_id]["pokemon"][index]
  
  def get_pokemon_by_id(self, pokemon_id):
    """
    Descobre os dados de um Pokémon a partir de um ID.
    Args:
      pokemon_id: ID do Pokémon a ser consultado.
    Returns:
      Os dados detalhados do Pokémon consultado.
    """
    for index, pokemon in enumerate(self.pokedex):
      if pokemon["id"] == pokemon_id:
        return pokemon
  
  def get_pokemon_by_name(self, pokemon_name):
    """
    Descobre os dados de um Pokémon a partir de um nome.
    Args:
      pokemon_name: Nome do Pokémon a ser consultado.
    Returns:
      Os dados detalhados do Pokémon consultado.
    """
    for index, pokemon in enumerate(self.pokedex):
        current_name = str(pokemon["name"]["english"]).lower()
        pokemon_name = str(pokemon_name).lower()
        if current_name == pokemon_name:
          return pokemon
  

  def translate_party_to_pokemon_data(self, party):
    """
    Tradus uma lista de IDs para lista de dados de Pokémon.
    Args:
      party: lista de IDs de Pokémon
    Returns:
      Lista de dados de Pokémon.
    """
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

  def add_individual_pokemon(self):
    """
    Método auxiliar do menu para a ação de adicionar Pokémon individual
    Returns:
      Próximo passo a ser executado no menu.
    """
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
    
    print(f"O Pokémon que você escolheu é")
    self.print_poke(pokemon)
    print("Confirma? [s/n]")
    resposta = input()
    if resposta.lower() == "s":
      self.push_pokemon(0, pokemon)
      return 0  # Retorna à etapa 0
    else:
      return 1  # Volta à etapa 1

  # Função para adicionar uma party inteira (ETAPA 2)
  def adicionar_party(self):
    """
    Método auxiliar do menu para a ação de adicionar party inteira.
    Returns:
      Próximo passo a ser executado no menu.
    """
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
    """
    Calcula o multiplicador de efetividade de tipo.
    Args:
      pokemon_a_types: Lista de tipos do Pokémon A
      pokemon_b_types: Lista de tipos do Pokémon B
    Returns:
      Multiplicador de efetividade.
    """
    result = 1.0
    # aqui checamos em cada entrada do dicionário para verificar os multiplicadores de tipo
    for ef_a in pokemon_a_types:
      for ef_b in pokemon_b_types:
        result *= type_effectiveness[ef_a].get(ef_b, 1.0) # caso não haja nenhuma entrada no dicionário para o tipo atual, multiplicamos por 1.0

    if result > 1.0:
      print("O ataque foi super efetivo!")
    return result

  # Aqui calculamos o dano aplicado de um pokemon ao outro, de acordo com a fórmula descrita em https://bulbapedia.bulbagarden.net/wiki/Damage
  def calculate_damage(self, pokemon_a, pokemon_b):
    """
    Cálcula o dano de um Pokémon A a um Pokémon B, de acordo com a fórmula descrita no link acima.
    Args:
      pokemon_a: Dados do Pokémon A (Atacante)
      pokemon_b: Dados do Pokémon B (Defensor)
    Returns:
      Dano causado ao Pokémon B.
    """
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
    """
    Método auxiliar do menu para a ação de listar todos os Pokémon.
    Returns:
      Próximo passo a ser executado no menu.
    """
    for o in self.pokedex:
      print(f"{o['id']} - {o['name']['english']}")
    return 0  # Volta à etapa 0

  # Função para consultar dados de um Pokémon específico (ETAPA 4)
  def consultar_pokemon(self):
    """
    Método auxiliar do menu para a ação de consultar um Pokémon específico.
    Returns:
      Próximo passo a ser executado no menu.
    """
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
    """
    Menu de jogo, aqui o jogador será apresentado as opções possíveis.
    Returns:
      0 caso seja para finalizar o jogo, ou 1, caso contrário.
    """
    
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
        print("0 - Sair")
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
        elif opcao == "0":
           return 0

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
    return 1


  def get_ids_from_party(self, party):
    """
    Traduz uma lista de Pokémon para uma lista de IDs.
    Args:
      party: Lista de Pokémon.
    Returns:
      Lista de IDs relacionados aos Pokemon de 'party' (e na mesma ordem).
    """
    ids = []
    for poke in party:
      ids.append(poke["id"])
    return ids
  