"""
player.py

Authors: Thiago Ferronatto and Yuri Moraes Gavilan

This file contains the main interface through which the average user is going to
interact with the system. It provides simple text-based menus for navigating
through the extremely simple operations that the application can perform,
including access to the Pokémon Netventures battle simulation game.
"""


from ias_interface_data import *
from mms_interface_data import *
from socket import *
from style import *
import sys
from game import GameState
import time
import pickle


class LogMessage:
    """
    A class that contains methods for generating log messages for the player
    client.
    """

    def bad_usage():
        return f"{Style.fail('[ERRO]')} Uso: python player.py"

    def incorrect_credentials(username):
        return f"{Style.fail('[ERRO]')} Credenciais incorretas para o usuário {Style.bold(username)}."

    def user_already_exists(username):
        return f"{Style.fail('[ERRO]')} Usuário {Style.bold(username)} já existe."

    def logged_out(username):
        return (
            f"{Style.blue('[INFO]')} Logout como {Style.bold(username)} bem-sucedido."
        )

    def already_logged_out(username):
        return f"{Style.fail('[ERRO]')} Logout como {Style.bold(username)} falhou; esse usuário não está logado."

    def auth_failed(username):
        return f"{Style.fail('[ERRO]')} Token de autenticação inválido para {Style.bold(username)}."

    def looking_for_match():
        return f"{Style.blue('[INFO]')} Procurando partida..."

    def matchmaking_error():
        return f"{Style.fail('[ERRO]')} Erro desconhecido no servidor de matchmaking."

    def accept_match():
        return f"{Style.pink('[ENTRADA]')} Partida encontrada. Aceitar? [s/n] "

    def match_declined_by_another():
        return f"{Style.warn('[AVISO]')} Partida recusada por outro jogador."

    def match_declined():
        return f"{Style.fail('[ERRO]')} Você recusou a partida."

    def invalid_answer():
        return f"{Style.fail('[ERRO]')} Resposta inválida."


def login(username, password):
    """
    Attempts to authenticate a user with the IAS server using a username and
    password. If successful, returns a token that can be used for further
    communication with the server. If unsuccessful, prints an error message and
    exits the program.

    Parameters
    ----------
    username : str
        The username of the user who wants to log in.
    password : str
        The password of the user who wants to log in.

    Returns
    -------
    str or None
        The authentication token as a hexadecimal string if login is successful,
        or None otherwise.
    """
    auth_socket = socket()
    auth_socket.connect((IAS_ADDRESS, IAS_PORT))
    msg = str(IasOpCode.AUTHENTICATE) + IAS_OPCODE_ARGS_SEP + username + " " + password
    auth_socket.send(msg.encode())
    buflen = IAS_OPCODE_SIZE + IAS_AUTH_TOKEN_HEX_STR_LENGTH + 1
    response = auth_socket.recv(buflen).decode().split(" ")
    status = int(response[0])
    token = None
    if status == IasResponse.LOGIN_SUCCESSFUL:
        token = response[1]
    else:
        print(LogMessage.incorrect_credentials(username))
        auth_socket.close()
        exit(1)
    auth_socket.close()
    return token


def register(username, password, name):
    """
    Attempts to register a new user with the IAS server using a username,
    password, and name. If successful, returns a token that can be used for
    further communication with the server. If unsuccessful, prints an error
    message and exits the program.

    Parameters
    ----------
    username : str
        The username of the new user who wants to register.
    password : str
        The password of the new user who wants to register.
    name : str
        The name of the new user who wants to register.

    Returns
    -------
    str or None
        The authentication token as a hexadecimal string if registration is
        successful, or None otherwise.
    """
    auth_socket = socket()
    auth_socket.connect((IAS_ADDRESS, IAS_PORT))
    msg = str(IasOpCode.REGISTER) + IAS_OPCODE_ARGS_SEP + username + " " + password
    msg += " " + name
    auth_socket.send(msg.encode())
    buflen = IAS_OPCODE_SIZE + IAS_AUTH_TOKEN_HEX_STR_LENGTH + 1
    response = auth_socket.recv(buflen).decode().split(" ")
    status = int(response[0])
    token = None
    if status == IasResponse.LOGIN_SUCCESSFUL:
        token = response[1]
    else:
        print(LogMessage.user_already_exists(username))
        auth_socket.close()
        exit(1)
    auth_socket.close()
    return token


def logout(token, username):
    """
    Attempts to log out a user from the IAS server using a token and a username.
    If successful, prints a confirmation message and closes the connection. If
    unsuccessful, prints an error message and exits the program.

    Parameters
    ----------
    token : str
        The authentication token of the user who wants to log out.
    username : str
        The username of the user who wants to log out.
    """
    auth_socket = socket()
    auth_socket.connect((IAS_ADDRESS, IAS_PORT))
    msg = str(IasOpCode.LOGOUT) + IAS_OPCODE_ARGS_SEP + token + " " + username
    auth_socket.send(msg.encode())
    status = int(auth_socket.recv(IAS_OPCODE_SIZE).decode())
    if status == IasResponse.LOGOUT_SUCCESSFUL:
        print(LogMessage.logged_out(username))
    else:
        print(LogMessage.already_logged_out(username))
        auth_socket.close()
        exit(1)
    auth_socket.close()


def look_for_match(token, username):
    """
    Attempts to find a match for a user with the matchmaking server using a
    token and a username. If successful, returns a tuple of the IP address, port
    number, and server port of the match. If unsuccessful, prints an error
    message and exits the program.

    Parameters
    ----------
    token : str
        The authentication token of the user who wants to find a match.
    username : str
        The username of the user who wants to find a match.

    Returns
    -------
    tuple or None
        A tuple of the form (ip, port, server_port) if a match is found, or None
        otherwise.
    """
    mm_addr = (MATCHMAKING_ADDRESS, MATCHMAKING_PORT)
    matchmaking_socket = socket(AF_INET, SOCK_DGRAM)

    msg = str(MmsOpCode.MAKE_AVAILABLE) + MMS_OPCODE_ARGS_SEP + token + " "
    msg += username
    matchmaking_socket.sendto(msg.encode(), mm_addr)
    response = int(matchmaking_socket.recv(MMS_RESPONSE_CODE_SIZE).decode())

    if response == MmsResponse.USER_NOT_AUTHENTICATED:
        print(LogMessage.auth_failed(username))
        matchmaking_socket.close()
        logout(token, username)
        exit(1)
    elif response == MmsResponse.IN_QUEUE:
        print(LogMessage.looking_for_match())
    else:
        print(LogMessage.matchmaking_error())
        matchmaking_socket.close()
        logout(token, username)
        exit(1)

    in_queue = True
    while in_queue:
        response, addr = matchmaking_socket.recvfrom(MMS_RESPONSE_CODE_SIZE)

        response = int(response.decode())

        answer = None
        ip, port, server_port = None, None, None
        if response == MmsResponse.MATCH_AVAILABLE:
            answer = input(LogMessage.accept_match())
            if answer == "s":
                matchmaking_socket.sendto(str(MmsOpCode.ACCEPT_MATCH).encode(), addr)
                response = (
                    matchmaking_socket.recv(
                        MMS_RESPONSE_CODE_SIZE + 15 * 2 + 5 * 4 + 2  # dont even ask
                    )
                    .decode()
                    .split(MMS_RESPONSE_CODE_ARGS_SEP)
                )

                respcode = int(response[0])

                if respcode == MmsResponse.MATCH_READY:
                    args = response[1].split(" ")
                    ip, port = args[0], int(args[1])
                    if len(args) == 3:
                        server_port = int(args[2])
                    in_queue = False
                    return (ip, port, server_port)
                elif respcode == MmsResponse.OTHER_PLAYER_DECLINED:
                    print(LogMessage.match_declined_by_another())
                    print(LogMessage.looking_for_match())
                else:
                    print(LogMessage.matchmaking_error())
                    matchmaking_socket.close()
                    logout(token, username)
                    exit(1)
            elif answer == "n":
                matchmaking_socket.sendto(str(MmsOpCode.DECLINE_MATCH).encode(), addr)
                response = int(matchmaking_socket.recv(MMS_RESPONSE_CODE_SIZE).decode())
                if response == MmsResponse.FAILED_TO_ACCEPT:
                    print(LogMessage.match_declined())
                    matchmaking_socket.close()
                    logout(token, username)
                    exit(1)
                else:
                    print(LogMessage.matchmaking_error())
                    matchmaking_socket.close()
                    logout(token, username)
                    exit(1)
            else:
                print(LogMessage.invalid_answer())
                matchmaking_socket.close()
                logout(token, username)
                exit(1)
        else:
            print(LogMessage.matchmaking_error())
            matchmaking_socket.close()
            logout(token, username)
            exit(1)

    matchmaking_socket.close()


def list_online_players(token, username):
    """
    Requests the list of online users from the IAS server using a token and a
    username. If successful, prints the list of online users in a formatted way.
    If unsuccessful, prints an error message and exits the program.

    Parameters
    ----------
    token : str
        The authentication token of the user who wants to see the list of online
        users.
    username : str
        The username of the user who wants to see the list of online users.
    """
    auth_socket = socket()
    auth_socket.connect((IAS_ADDRESS, IAS_PORT))
    msg = str(IasOpCode.LIST_USERS)
    auth_socket.send(msg.encode())
    response = auth_socket.recv(1024).decode().split(IAS_RESPONSE_CODE_ARGS_SEP)
    print(response)

    if int(response[0]) == IasResponse.USER_LIST:
        user_list = response[1]
        print(
            "\n\n---------------\n"
            "Usuários online\n"
            "---------------\n\n"
            f"{user_list}"
        )
    else:
        print("Erro ao buscar a lista de usuários.")
        auth_socket.close()
        logout(token, username)
        exit(1)
    auth_socket.close()


def end_match(token, username):
    """
    Notifies the matchmaking server that a match has ended using a token and a
    username. If successful, prints a confirmation message and closes the
    connection. If unsuccessful, does nothing.

    Parameters
    ----------
    token : str
        The authentication token of the user who has ended the match.
    username : str
        The username of the user who has ended the match.
    """
    mm_addr = (MATCHMAKING_ADDRESS, MATCHMAKING_PORT)
    matchmaking_socket = socket(AF_INET, SOCK_DGRAM)
    msg = str(MmsOpCode.MATCH_ENDED) + MMS_OPCODE_ARGS_SEP + token + " "
    msg += username
    matchmaking_socket.sendto(msg.encode(), mm_addr)
    response = int(matchmaking_socket.recv(MMS_RESPONSE_CODE_SIZE).decode())
    matchmaking_socket.close()
    if response == MmsResponse.MATCH_ENDED:
        print("Partida encerrada.")


def list_ongoing_matches(token, username):
    """
    Requests the list of ongoing matches from the matchmaking server using a
    token and a username. If successful, prints the list of ongoing matches in a
    formatted way. If unsuccessful, does nothing.

    Parameters
    ----------
    token : str
        The authentication token of the user who wants to see the list of
        ongoing matches.
    username : str
        The username of the user who wants to see the list of ongoing matches.
    """
    mm_addr = (MATCHMAKING_ADDRESS, MATCHMAKING_PORT)
    matchmaking_socket = socket(AF_INET, SOCK_DGRAM)
    msg = str(MmsOpCode.LIST_MATCHES) + MMS_OPCODE_ARGS_SEP + token + " "
    msg += username
    matchmaking_socket.sendto(msg.encode(), mm_addr)
    response = matchmaking_socket.recv(4096).decode().split(MMS_RESPONSE_CODE_ARGS_SEP)
    matchmaking_socket.close()
    if int(response[0]) == MmsResponse.MATCH_LIST:
        match_list = response[1]
        print(match_list)


game_state = GameState()


def get_hp_text(original_health, hp) -> str:
    """
    Returns a formatted string of the current health of a player, based on the
    original health and the current health. The string is colored green, yellow,
    or red depending on the percentage of health remaining.

    Parameters
    ----------
    original_health : float
        The original health of the player at the start of the game.
    hp : float
        The current health of the player.

    Returns
    -------
    str
        The formatted string of the current health, with color and two decimal
        places.
    """
    result: str
    if hp >= original_health * 0.6:
        result = Style.green(f"{hp:.2f}")
    elif hp >= original_health * 0.3:
        result = Style.warn(f"{hp:.2f}")
    else:
        result = Style.red(f"{hp:.2f}")
    return result


def run_battle(game_socket: socket, my_turn: bool):
    """
    Runs the main loop of the battle game, where each player takes turns to deal
    damage to the opponent's pokemon.The game ends when one player runs out of
    pokemon or quits the game. The game_socket is used to send and receive
    messages between the players. The my_turn parameter indicates whether it is
    the current player's turn or not.

    Parameters
    ----------
    game_socket : socket
        The socket object that connects the current player with the opponent.
    my_turn : bool
        A boolean value that indicates whether it is the current player's turn
        or not.
    """
    game_running = True

    print(Style.blue(f"Seu adversário é: \"{game_state.player[1]['name']}\""))
    while game_running:
        time.sleep(
            0.5
        )  # A thread dorme por 0.5 segundos para simular a experiência de uma batalha Pokémon em turnos.

        player_current_pokemon = game_state.player[0]["pokemon"][
            0
        ]  # Atual Pokémon do jogador
        enemy_current_pokemon = game_state.player[1]["pokemon"][
            0
        ]  # Atual Pokémon do adversário

        if my_turn:
            """
            Caso my_turn seja verdadeiro, o jogador local será o responsável por atacar.
            Calculamos o dano localmente, e o enviamos ao outro jogador.
            Após isso, imprimimos a mensagem de quanto dano foi causado ao Pokémon adversário.
            """
            damage_dealt = game_state.calculate_damage(
                player_current_pokemon, enemy_current_pokemon
            )
            game_socket.send(str(damage_dealt).encode())
            game_state.player[1]["hp_data"][0] -= damage_dealt

            player_hp_text = get_hp_text(
                game_state.player[0]["pokemon"][0]["base"]["HP"],
                game_state.player[0]["hp_data"][0],
            )
            enemy_hp_text = get_hp_text(
                game_state.player[1]["pokemon"][0]["base"]["HP"],
                game_state.player[1]["hp_data"][0],
            )

            print(
                f"Seu {player_current_pokemon['name']['english']} ({player_hp_text} HP) causou {damage_dealt:.2f} de dano em {enemy_current_pokemon['name']['english']} ({enemy_hp_text} HP)"
            )
        else:
            """
            Caso my_turn seja falso, o jogador adversário será o responsável por atacar.
            Esperamos pela mensagem no socket, e, ao recebê-la, atualizamos o estado local.
            Após isso, imprimimos a mensagem de quanto dano foi causado ao Pokémon local.
            """
            damage_received_message = game_socket.recv(1024).decode()
            game_state.player[0]["hp_data"][0] -= float(damage_received_message)

            player_hp_text = get_hp_text(
                game_state.player[0]["pokemon"][0]["base"]["HP"],
                game_state.player[0]["hp_data"][0],
            )
            enemy_hp_text = get_hp_text(
                game_state.player[1]["pokemon"][0]["base"]["HP"],
                game_state.player[1]["hp_data"][0],
            )

            print(
                f"Seu {player_current_pokemon['name']['english']} ({player_hp_text} HP) sofreu {float(damage_received_message):.2f} de dano de {enemy_current_pokemon['name']['english']} ({enemy_hp_text} HP)"
            )

        # Flipando o turno (se for false vira true e vice-versa)
        my_turn = not my_turn

        # Verifica se algum Pokemon foi derrotado, caso sim, ele é removido da fila
        for i in range(0, 2):
            if game_state.player[i]["hp_data"][0] <= 0:
                if i == 0:
                    print(
                        Style.red(
                            f"Seu {game_state.player[i]['pokemon'][0]['name']['english']} desmaiou! :("
                        )
                    )
                else:
                    print(
                        Style.green(
                            f"O {game_state.player[i]['pokemon'][0]['name']['english']} do adversário desmaiou!"
                        )
                    )
                print("==========================================")
                del game_state.player[i]["hp_data"][0]
                del game_state.player[i]["pokemon"][0]

            if len(game_state.player[i]["pokemon"]) < 1:
                if i == 0:
                    print(Style.red("Você foi derrotado :("))
                else:
                    print(Style.green("Você venceu! :)"))
                game_running = False
                break


def main():
    """
    Runs the main menu of the game, where the user can choose to log in,
    register, or exit. If the user logs in or registers, they can then access
    the game menu, where they can choose to look for a match, list online users,
    list ongoing matches, or exit. If the user looks for a match, they will be
    connected with another player and start a battle game using pokemon. The
    user can be either the server or the client of the game, depending on who
    was first in queue in the matchmaking server. The user can quit the game at
    any time by choosing the exit option.
    """
    op = int(input("1. Fazer login\n2. Fazer cadastro\n\n0. Sair\n\n: "))

    if op == 0:
        return

    token = None
    username = input("\n\nNome de usuário: ")
    password = input("Senha: ")
    if op == 1:
        token = login(username, password)
    elif op == 2:
        name = input("Nome completo: ")
        token = register(username, password, name)

    while True:
        for i in range(0, 2):
            game_state.player[i]["pokemon"].clear()

        if game_state.menu() == 1:
            op = int(
                input(
                    "\n\n"
                    "1. Procurar partida\n"
                    "2. Listar usuários online\n"
                    "3. Listar partidas em andamento\n\n"
                    "0. Sair"
                    "\n\n: "
                )
            )
        else:
            op = 0

        match_addr_info = ()
        if op == 1:
            match_addr_info = look_for_match(token, username)
        elif op == 2:
            list_online_players(token, username)
            continue
        elif op == 3:
            list_ongoing_matches(token, username)
            continue
        elif op == 0:
            break
        ip, port, server_port = match_addr_info

        print(f"other player @ {ip}:{port}")

        your_party = game_state.player[0]["pokemon"]

        """
        Um dos jogadores inicia como 'servidor', ou seja, inicia esperando a abordagem do outro jogador que atua como 'cliente', algo que irá se alternando.
        Inicialmente, os jogadores trocam mensagens para compartilhar entre si os dados locais: o nome dos jogadores e o time de cada um deles. Estes dados são, então,
        armazenados localmente em game_state.
        """

        if server_port:  # you are the server (player 1)
            # Aqui fazemos a conexão com o outro jogador
            server_socket = socket(AF_INET, SOCK_STREAM)
            server_socket.bind(("", server_port))
            server_socket.listen(1)
            game_socket, _ = server_socket.accept()

            # Armazenamos o username do jogador local
            game_state.player[0]["name"] = username

            # Armazenamos o username do adversário
            game_state.player[1]["name"] = game_socket.recv(1024).decode()

            # Enviamos o username do jogador local ao adversário
            game_socket.send(username.encode())

            # ================== PREPARATION =====================

            # Recebemos o time do adversário (lista de IDs de Pokémon)
            opponent_party = game_socket.recv(1024)
            # Usamos o pickle apenas para desserializar os dados recebidos
            opponent_party = pickle.loads(opponent_party)

            # Traduzimos os IDs em uma lista de Pokémon
            opponent_party = game_state.translate_party_to_pokemon_data(opponent_party)

            # Adicionamos o time ao estado local
            game_state.add_party_to_player(opponent_party, 1)

            # Obtemos uma lista de IDs a partir do nosso time local.
            your_party_ids = game_state.get_ids_from_party(your_party)

            # Serializamos a lista de IDs para enviar pelo socket.
            data = pickle.dumps(your_party_ids)

            # Enviamos a lista pelo socket
            game_socket.send(data)

            # ================== GAME BEGINS =====================

            # Não iniciamos jogando, e damos inicio à partida.
            my_turn = False
            run_battle(game_socket, my_turn)

            # ================== GAME ENDS =====================

            # O socket é fechado
            game_socket.close()
            server_socket.close()

            input("Pressione [Enter] para encerrar a partida")

            end_match(token, username)
        else:  # the other player is the server (you are player 2)
            game_socket = socket()
            game_socket.connect((ip, port))

            # Enviamos o nosso username ao adversário, recebemos o username dele, e armazenamos os dados localmente
            game_socket.send(username.encode())
            game_state.player[0]["name"] = username
            game_state.player[1]["name"] = game_socket.recv(1024).decode()

            # ================== PREPARATION =====================

            # Obtemos uma lista de IDs a partir do nosso time local.
            your_party_ids = game_state.get_ids_from_party(your_party)
            # Serializamos a lista de IDs para enviar pelo socket.
            data = pickle.dumps(your_party_ids)
            # Enviamos a lista pelo socket
            game_socket.send(data)

            # Recebemos o time do adversário (lista de IDs de Pokémon)
            opponent_party = game_socket.recv(1024)
            # Usamos o pickle apenas para desserializar os dados recebidos
            opponent_party = pickle.loads(opponent_party)

            # Traduzimos os IDs em uma lista de Pokémon
            opponent_party = game_state.translate_party_to_pokemon_data(opponent_party)

            # Adicionamos o time ao estado local
            game_state.add_party_to_player(opponent_party, 1)

            # ================== GAME BEGINS =====================

            # Iniciamos jogando, e damos inicio à partida.
            my_turn = True
            run_battle(game_socket, my_turn)

            # ================== GAME ENDS =====================

            game_socket.close()

    logout(token, username)


if __name__ == "__main__":
    main()
