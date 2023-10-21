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


def authenticate(username, password):
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


def main():
    if len(sys.argv) < 3:
        print(LogMessage.bad_usage())
        return
    username = sys.argv[1]
    password = sys.argv[2]  # would benefit from an encrypted connection
    token = None
    if len(sys.argv) > 3:
        token = register(username, password, sys.argv[3])
    else:
        token = authenticate(username, password)

    # at this point the player has a valid token, proceed to matchmaking server

    mm_addr = (MATCHMAKING_ADDRESS, MATCHMAKING_PORT)
    matchmaking_socket = socket(AF_INET, SOCK_DGRAM)

    msg = str(MmsOpCode.MAKE_AVAILABLE) + MMS_OPCODE_ARGS_SEP + token + " "
    msg += username
    matchmaking_socket.sendto(msg.encode(), mm_addr)
    response = int(matchmaking_socket.recv(MMS_RESPONSE_CODE_SIZE).decode())

    if response == MmsResponse.USER_NOT_AUTHENTICATED:
        print(LogMessage.auth_failed(username))
        exit(1)
        matchmaking_socket.close()
    elif response == MmsResponse.IN_QUEUE:
        print(LogMessage.looking_for_match())
    else:
        print(LogMessage.matchmaking_error())
        matchmaking_socket.close()
        exit(1)

    # I apologize in advance for how awful this next section is.

    in_queue = True
    while in_queue:
        response, addr = matchmaking_socket.recvfrom(MMS_RESPONSE_CODE_SIZE)

        response = int(response.decode())

        answer = None
        ip, port = None, None
        if response == MmsResponse.MATCH_AVAILABLE:
            answer = input(LogMessage.accept_match())
            if answer == "s":
                matchmaking_socket.sendto(str(MmsOpCode.ACCEPT_MATCH).encode(), addr)
                response = (
                    matchmaking_socket.recv(MMS_RESPONSE_CODE_SIZE + 15 * 2 + 5 * 2)
                    .decode()
                    .split(MMS_RESPONSE_CODE_ARGS_SEP)
                )

                respcode = int(response[0])

                if respcode == MmsResponse.MATCH_READY:
                    ip, port = response[1].split(" ")
                    port = int(port)
                    in_queue = False
                elif respcode == MmsResponse.OTHER_PLAYER_DECLINED:
                    print(LogMessage.match_declined_by_another())
                    print(LogMessage.looking_for_match())
                else:
                    print(LogMessage.matchmaking_error())
                    logout(token, username)
                    matchmaking_socket.close()
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
                    exit(1)
            else:
                print(LogMessage.invalid_answer())
                logout(token, username)
                matchmaking_socket.close()
                exit(1)
        else:
            print(LogMessage.matchmaking_error())
            logout(token, username)
            matchmaking_socket.close()
            exit(1)

    print(f"other player @ {ip}:{port}")

    # TODO: implement game logic, communicate through matchmaking_socket

    logout(token, username)

    matchmaking_socket.close()


if __name__ == "__main__":
    main()
