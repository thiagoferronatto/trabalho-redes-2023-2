# Player client


from ias_interface_data import *
from socket import *
from style import *
import sys


class LogMessage:
    def bad_usage():
        return f"{Style.fail("[ERRO]")} Uso: python player.py <nome de usuário> <senha> [<nome>]"

    def incorrect_credentials():
        return f"{Style.fail("[ERRO]")} Credenciais incorretas."

    def user_already_exists():
        return f"{Style.fail("[ERRO]")} Usuário {Style.bold(username)} já existe."


def authenticate(username, password):
    auth_socket = socket()
    auth_socket.connect(("127.0.0.1", IAS_PORT))
    msg = str(OpCode.AUTHENTICATE) + IAS_OPCODE_ARGS_SEP + username + " " + password
    auth_socket.send(msg.encode())
    buflen = IAS_OPCODE_SIZE + IAS_AUTH_TOKEN_HEX_STR_LENGTH + 1
    response = auth_socket.recv(buflen).decode().split(" ")
    status = int(response[0])
    token = None
    if status == Response.LOGIN_SUCCESSFUL:
        token = response[1]
    else:
        print(LogMessage.incorrect_credentials())
        exit(1)
    auth_socket.close()
    return token


def register(username, password, name):
    auth_socket = socket()
    auth_socket.connect((IAS_ADDRESS, IAS_PORT))
    msg = str(OpCode.REGISTER) + IAS_OPCODE_ARGS_SEP + username + " " + password
    msg += " " + name
    auth_socket.send(msg.encode())
    buflen = IAS_OPCODE_SIZE + IAS_AUTH_TOKEN_HEX_STR_LENGTH + 1
    response = auth_socket.recv(buflen).decode().split(" ")
    status = int(response[0])
    token = None
    if status == Response.LOGIN_SUCCESSFUL:
        token = response[1]
    else:
        print(LogMessage.user_already_exists(username))
        exit(1)
    auth_socket.close()
    return token


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

    # TODO: find match through MM server, then switch to P2P

    # TODO: implement game logic


if __name__ == "__main__":
    main()
