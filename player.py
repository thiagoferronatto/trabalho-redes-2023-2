# Player client


from ias_interface_data import *
from mms_interface_data import *
from socket import *
from style import *
import sys


class LogMessage:
    def bad_usage():
        return f"{Style.fail('[ERRO]')} Uso: python player.py <nome de usuário> <senha> [<nome>]"

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


def list_players(token, username):
    mm_addr = (MATCHMAKING_ADDRESS, MATCHMAKING_PORT)
    matchmaking_socket = socket(AF_INET, SOCK_DGRAM)

    msg = str(MmsOpCode.LIST_PLAYERS) + MMS_OPCODE_ARGS_SEP + token + " "
    msg += username
    matchmaking_socket.sendto(msg.encode(), mm_addr)
    response = (
        matchmaking_socket.recv(2**16).decode().split(MMS_RESPONSE_CODE_ARGS_SEP)
    )
    if int(response[0]) == MmsResponse.PLAYER_LIST:
        player_list = response[1]
        print(player_list)


def main():
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
        op = int(
            input(
                "\n\n"
                "1. Procurar partida\n"
                "2. Listar usuários online\n"
                "2. Listar partidas em andamento\n\n"
                "0. Sair"
                "\n\n: "
            )
        )

        match_addr_info = ()
        if op == 1:
            match_addr_info = look_for_match(token, username)
        elif op == 2:
            list_players(token, username)
            continue
        elif op == 3:
            continue
        elif op == 0:
            break
        ip, port, server_port = match_addr_info

        print(f"other player @ {ip}:{port}")

        if server_port:  # you are the server (player 1)
            server_socket = socket(AF_INET, SOCK_STREAM)
            server_socket.bind(("", server_port))
            server_socket.listen(1)
            game_socket, _ = server_socket.accept()

            # TODO: communicate with player 2 through game_socket
            msg = game_socket.recv(1024).decode()
            print(msg)

            game_socket.close()
            server_socket.close()
        else:  # the other player is the server (you are player 2)
            game_socket = socket()
            game_socket.connect((ip, port))

            # TODO: communicate with player 1 through game_socket
            game_socket.send("asdf".encode())

            game_socket.close()

    logout(token, username)


if __name__ == "__main__":
    main()
