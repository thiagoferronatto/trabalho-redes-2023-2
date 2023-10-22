# Information and Authentication Server


from ias_interface_data import *
from socket             import *
from argon2             import PasswordHasher  # python -m pip install argon2-cffi
from style              import *

import secrets
import enum


IAS_MAX_USERNAME_LENGTH = 256
IAS_MAX_PASSWORD_LENGTH = 256
IAS_MAX_NAME_LENGTH     = 1024
IAS_BACKLOG_SIZE        = 8

IAS_USERS_DB_PATH       = "users.db"
IAS_USERS_DB_SEP        = "|||"


class User:
    def __init__(__self__, username, password_hash, name):
        __self__.username      = username
        __self__.password_hash = password_hash
        __self__.name          = name


class LogMessage:
    def server_listening():
        return f"{Style.blue('[INFO]')} Servidor escutando pela porta {Style.bold(IAS_PORT)}."

    def login_successful(username):
        return f"{Style.blue('[INFO]')} Login bem-sucedido: usuário {Style.bold(username)} entrou."

    def wrong_credentials(username):
        return f"{Style.warn('[AVISO]')} Login falhou: Credenciais inválidas para {Style.bold(username)}."

    def no_such_user(username):
        return f"{Style.warn('[AVISO]')} Login falhou: Usuário {Style.bold(username)} não existe."

    def user_already_logged(username):
        return f"{Style.warn('[AVISO]')} Login falhou: Tentativa de relogar o usuário {Style.bold(username)}."

    def registration_successful(username):
        return f"{Style.blue('[INFO]')} Cadastro bem-sucedido: Usuário {Style.bold(username)} cadastrado."

    def user_already_exists(username):
        return f"{Style.warn('[AVISO]')} Cadastro falhou: Tentativa de recadastrar o usuário {Style.bold(username)}."

    def verification_successful(username):
        return f"{Style.blue('[INFO]')} Verificação bem-sucedida: usuário {Style.bold(username)} teve seu token validado."

    def verification_failed(username):
        return f"{Style.warn('[AVISO]')} Verificação falhou: usuário {Style.bold(username)} não possuia um token válido."

    def logout_successful(username):
        return f"{Style.blue('[INFO]')} Logout bem-sucedido: usuário {Style.bold(username)} saiu."

    def logout_failed(username):
        return f"{Style.warn('[AVISO]')} Logout falhou: usuário {Style.bold(username)} tentou sair, mas não estava logado."


def load_users():
    file = None
    try:
        file = open(IAS_USERS_DB_PATH, "r")
    except:
        return []
    users = []
    while line := " ".join(file.readline().split()):
        username, password_hash, name = line.split(IAS_USERS_DB_SEP)
        users.append(User(username, password_hash, name))
    file.close()
    return users


def save_users():
    file = open(IAS_USERS_DB_PATH, "w+")
    for user in registered_users:
        file.write(f"{user.username}{IAS_USERS_DB_SEP}{user.password_hash}{IAS_USERS_DB_SEP}{user.name}\n")
    file.close()


def token(username):
    auth_token = secrets.token_hex(IAS_AUTH_TOKEN_SIZE)
    logged_users[auth_token] = username
    return auth_token


def authenticate(username, password):
    matching_user = [
        user for user in registered_users if user.username == username
    ]
    if not matching_user:
        print(LogMessage.no_such_user(username))
        return None
    try:
        hasher.verify(matching_user[0].password_hash, password)
        if username in logged_users.values():
            print(LogMessage.user_already_logged(username))
            return None
        print(LogMessage.login_successful(username))
        return token(username)
    except:  # hasher throws a tantrum if the password is wrong
        print(LogMessage.wrong_credentials(username))
        return None


def auth_response(username, password):
    if tk := authenticate(username, password):
        return str(IasResponse.LOGIN_SUCCESSFUL) + " " + tk
    return str(IasResponse.LOGIN_FAILED)


def register(username, password_hash, name):
    matching_user = [
        user for user in registered_users if user.username == username
    ]
    if matching_user:
        print(LogMessage.user_already_exists(username))
        return IasResponse.USER_ALREADY_EXISTS
    registered_users.append(User(username, password_hash, name))
    save_users()  # rewrites the whole thing
    print(LogMessage.registration_successful(username))
    return IasResponse.REGISTRATION_SUCCESSFUL


def verify(token, username):
    if logged_users[token] == username:
        print(LogMessage.verification_successful(username))
        return IasResponse.VERIFICATION_SUCCESSFUL
    print(LogMessage.verification_failed(username))
    return IasResponse.VERIFICATION_FAILED


def logout(token, username):
    if logged_users[token] == username:
        del(logged_users[token])
        print(LogMessage.logout_successful(username))
        return IasResponse.LOGOUT_SUCCESSFUL
    print(LogMessage.logout_failed(username))
    return IasResponse.LOGOUT_FAILED


registered_users = load_users()
logged_users     = {}
hasher           = PasswordHasher()


def main():
    server_socket = socket(AF_INET, SOCK_STREAM)
    server_socket.bind(("", IAS_PORT))
    server_socket.listen(IAS_BACKLOG_SIZE)

    print(LogMessage.server_listening())

    while True:
        connection_socket, client_address = server_socket.accept()
        buflen = IAS_OPCODE_SIZE + IAS_MAX_USERNAME_LENGTH + len(IAS_OPCODE_ARGS_SEP)
        buflen += IAS_MAX_PASSWORD_LENGTH + IAS_MAX_NAME_LENGTH
        op_and_args = connection_socket.recv(buflen).decode().split(IAS_OPCODE_ARGS_SEP)
        opcode = op_and_args[0]
        args = None
        if len(op_and_args) > 1:
            args = op_and_args[1]

        opcode = int(opcode)

        if opcode == IasOpCode.AUTHENTICATE:  # args are username and password
            username, password = args.split(" ")
            connection_socket.send(auth_response(username, password).encode())
        elif opcode == IasOpCode.LOGOUT: # args are token and username
            token, username = args.split(" ")
            status = logout(token, username)
            connection_socket.send(str(status).encode())
        elif opcode == IasOpCode.REGISTER:  # args are username, password and name
            username, password, name = args.split(" ")
            status = register(username, hasher.hash(password), name)
            if status == IasResponse.REGISTRATION_SUCCESSFUL:
                connection_socket.send(auth_response(username, password).encode())
            else:
                connection_socket.send(str(status).encode())
        elif opcode == IasOpCode.VERIFY:  # args are token and username
            token, username = args.split(" ")
            status = verify(token, username)
            connection_socket.send(str(status).encode())

        connection_socket.close()


if __name__ == "__main__":
    main()
