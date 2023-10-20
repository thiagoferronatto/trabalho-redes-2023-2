# Player client


from socket import *
from style import *
import sys


IAS_PORT = 1234


def authenticate(username: str, password_hash: str, name: str = None):
    auth_socket = socket()
    auth_socket.connect(("127.0.0.1", IAS_PORT))
    auth_socket.send((username + " " + password_hash).encode())
    response = int(auth_socket.recv(4))
    if response == 0:  # auth successful
        print(f"{Style.blue("[INFO]")} Login bem-sucedido.")
    elif response == 1:  # wrong password
        print(f"{Style.fail("[ERRO]")} Senha incorreta.")
    elif response == 2:  # user does not exist, provide a full name to sign up
        if name == None or name == "":
            print(f"{Style.blue("[INFO]")} Usuário não encontrado. Vamos fazer seu cadastro!")
            name = input(f"{Style.pink("[ENTRADA]")} Nome completo: ")
            print(f"{Style.blue("[INFO]")} Cadastro realizado!")
        auth_socket.send(name.encode())


def main():
    username = sys.argv[1]
    password = sys.argv[2]  # would benefit from an encrypted connection
    if len(sys.argv) > 3:
        name = sys.argv[3]
    authenticate(username, password)


if __name__ == "__main__":
    main()
