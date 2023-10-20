# Information and Authentication Server


from socket import *
from style import *
from ports import *
import enum
from argon2 import PasswordHasher  # python -m pip install argon2-cffi

IAS_BACKLOG_SIZE = 8
IAS_MAX_USERNAME_LENGTH = 256
IAS_MAX_PASSWORD_LENGTH = 256
IAS_MAX_NAME_LENGTH = 1024
IAS_USERS_DB_PATH = "users.db"
IAS_USERS_DB_SEPARATOR = "|||"


class Response:
    LOGIN_SUCCESSFUL = b"0"
    WRONG_CREDENTIALS = b"1"
    USER_NOT_FOUND = b"2"


class User:
    def __init__(__self__, username, password_hash, name):
        __self__.username = username
        __self__.password_hash = password_hash
        __self__.name = name


def load_users(file_path):
    file = None
    try:
        file = open(file_path, "r")
    except:
        return []
    users = []
    while line := " ".join(file.readline().split()):
        fields = line.split(IAS_USERS_DB_SEPARATOR)
        username = fields[0]
        password_hash = fields[1]
        name = fields[2]
        users.append(User(username, password_hash, name))
    file.close()
    return users


def save_users(users, file_path):
    file = open(file_path, "w+")
    for user in users:
        file.write(f"{user.username}{IAS_USERS_DB_SEPARATOR}{user.password_hash}{IAS_USERS_DB_SEPARATOR}{user.name}\n")
    file.close()


def main():
    users = load_users(IAS_USERS_DB_PATH)
    hasher = PasswordHasher()

    server_socket = socket(AF_INET, SOCK_STREAM)
    server_socket.bind(("", IAS_PORT))
    server_socket.listen(IAS_BACKLOG_SIZE)
    print(
        f"{Style.blue("[INFO]")} Servidor escutando na porta {Style.bold(IAS_PORT)} por requisições."
    )

    while True:
        connection_socket, client_address = server_socket.accept()
        username, password = connection_socket.recv(
            IAS_MAX_USERNAME_LENGTH + IAS_MAX_PASSWORD_LENGTH + 1).decode().split(" ")
        matching_user = [
            user for user in users if user.username == username
        ]
        if matching_user:
            try:
                hasher.verify(matching_user[0].password_hash, password)
                connection_socket.send(Response.LOGIN_SUCCESSFUL)
                print(
                    f"{Style.blue("[INFO]")} Login bem-sucedido: usuário {Style.bold(username)} entrou do IP {Style.bold(client_address[0])}."
                )
            except: # hasher throws a tantrum if password is wrong
                connection_socket.send(Response.WRONG_CREDENTIALS)
                print(
                    f"{Style.warn("[WARNING]")} Autenticação falhou: Credenciais inválidas para {Style.bold(username)} do IP {Style.bold(client_address[0])}."
                )
        else:
            connection_socket.send(Response.USER_NOT_FOUND)
            name = connection_socket.recv(IAS_MAX_NAME_LENGTH).decode()
            users.append(User(username, hasher.hash(password), name))

            save_users(users, IAS_USERS_DB_PATH)  # rewrites the whole thing

            print(
                f"{Style.blue("[INFO]")} Cadastro: Usuário {Style.bold(username)} cadastrado do IP {Style.bold(client_address[0])}."
            )
        connection_socket.close()


if __name__ == "__main__":
    main()
