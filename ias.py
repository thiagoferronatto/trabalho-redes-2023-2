# Information and Authentication Server


from ias_interface_data import *
from logger import *
from socket import *
from argon2 import PasswordHasher  # python -m pip install argon2-cffi
from style import *

import secrets
import enum


IAS_MAX_USERNAME_LENGTH = 256
IAS_MAX_PASSWORD_LENGTH = 256
IAS_MAX_NAME_LENGTH = 1024
IAS_BACKLOG_SIZE = 8

IAS_USERS_DB_PATH = "users.db"
IAS_LOG_FILE_PATH = "ias.log"
IAS_USERS_DB_SEP = "|||"


class User:
    def __init__(__self__, username, password_hash, name):
        __self__.username = username
        __self__.password_hash = password_hash
        __self__.name = name


class LogMessage:
    """
    A class that contains methods for generating log messages for the IAS.
    """

    def server_listening():
        return f"Servidor escutando pela porta {IAS_PORT}."

    def login_successful(username):
        return f"Login bem-sucedido: usuário {username} entrou."

    def wrong_credentials(username):
        return f"Login falhou: Credenciais inválidas para {username}."

    def no_such_user(username):
        return f"Login falhou: Usuário {username} não existe."

    def user_already_logged(username):
        return f"Login falhou: Tentativa de relogar o usuário {username}."

    def registration_successful(username):
        return f"Cadastro bem-sucedido: Usuário {username} cadastrado."

    def user_already_exists(username):
        return f"Cadastro falhou: Tentativa de recadastrar o usuário {username}."

    def verification_successful(username):
        return f"Verificação bem-sucedida: usuário {username} teve seu token validado."

    def verification_failed(username):
        return f"Verificação falhou: usuário {username} não possuia um token válido."

    def logout_successful(username):
        return f"Logout bem-sucedido: usuário {username} saiu."

    def logout_failed(username):
        return f"Logout falhou: usuário {username} tentou sair, mas não estava logado."


def load_users():
    """
    Loads the users from the IAS users database file and returns them as a list
    of User objects.

    Returns
    -------
    list
        A list of User objects representing the users in the database.
    """
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
    """
    Saves the users to the IAS users database file.
    """
    file = open(IAS_USERS_DB_PATH, "w+")
    for user in registered_users:
        file.write(
            f"{user.username}{IAS_USERS_DB_SEP}{user.password_hash}{IAS_USERS_DB_SEP}{user.name}\n"
        )
    file.close()


def token(username):
    """
    Generates a random authentication token for a given username and stores it
    in the logged_users dictionary.

    Parameters
    ----------
    username : str
        The username of the user who needs a token.

    Returns
    -------
    str
        The authentication token as a hexadecimal string.
    """
    auth_token = secrets.token_hex(IAS_AUTH_TOKEN_SIZE)
    logged_users[auth_token] = username
    return auth_token


def authenticate(username, password):
    """
    Authenticates a user by checking their username and password against the
    registered users.

    Parameters
    ----------
    username : str
        The username of the user who wants to log in.
    password : str
        The password of the user who wants to log in.

    Returns
    -------
    str or None
        The authentication token for the user if they are authenticated, or None
        otherwise.
    """
    matching_user = [user for user in registered_users if user.username == username]
    if not matching_user:
        logger.log(LogMessage.no_such_user(username), Logger.WARNING)
        return None
    try:
        hasher.verify(matching_user[0].password_hash, password)
        if username in logged_users.values():
            logger.log(LogMessage.user_already_logged(username), Logger.WARNING)
            return None
        logger.log(LogMessage.login_successful(username), Logger.INFO)
        return token(username)
    except:  # hasher throws a tantrum if the password is wrong
        logger.log(LogMessage.wrong_credentials(username), Logger.WARNING)
        return None


def auth_response(username, password):
    """
    Returns a response code and a token for a user who tries to log in with
    their username and password.

    Parameters
    ----------
    username : str
        The username of the user who wants to log in.
    password : str
        The password of the user who wants to log in.

    Returns
    -------
    str
        A string containing the response code and the token (if successful),
        separated by a space.
    """
    if token := authenticate(username, password):
        return str(IasResponse.LOGIN_SUCCESSFUL) + " " + token
    return str(IasResponse.LOGIN_FAILED)


def register(username, password_hash, name):
    """
    Registers a new user with the given username, password hash, and name.

    Parameters
    ----------
    username : str
        The username of the new user.
    password_hash : str
        The hashed password of the new user.
    name : str
        The name of the new user.

    Returns
    -------
    int
        The response code for successful or failed registration.
    """
    matching_user = [user for user in registered_users if user.username == username]
    if matching_user:
        logger.log(LogMessage.user_already_exists(username), Logger.WARNING)
        return IasResponse.USER_ALREADY_EXISTS
    registered_users.append(User(username, password_hash, name))
    save_users()  # rewrites the whole thing
    logger.log(LogMessage.registration_successful(username), Logger.INFO)
    return IasResponse.REGISTRATION_SUCCESSFUL


def verify(token, username):
    """
    Verifies a user by checking their token and username.

    Parameters
    ----------
    token : str
        The authentication token of the user.
    username : str
        The username of the user.

    Returns
    -------
    int
        The response code for successful or failed verification.
    """
    if logged_users[token] == username:
        logger.log(LogMessage.verification_successful(username), Logger.INFO)
        return IasResponse.VERIFICATION_SUCCESSFUL
    logger.log(LogMessage.verification_failed(username), logger.WARNING)
    return IasResponse.VERIFICATION_FAILED


def logout(token, username):
    """
    Logs out a user.

    Parameters
    ----------
    token : str
        The authentication token of the user.
    username : str
        The username of the user.

    Returns
    -------
    int
        The response code for successful or failed logout.
    """
    if logged_users[token] == username:
        del logged_users[token]
        logger.log(LogMessage.logout_successful(username), Logger.INFO)
        return IasResponse.LOGOUT_SUCCESSFUL
    logger.log(LogMessage.logout_failed(username), Logger.WARNING)
    return IasResponse.LOGOUT_FAILED


registered_users = load_users()
logged_users = {}
hasher = PasswordHasher()
logger = Logger(IAS_LOG_FILE_PATH)


def main():
    """
    Starts the IAS server and handles requests from clients.

    The server uses TCP sockets to communicate with the clients and performs
    different operations based on the opcodes sent by them.The server supports
    the following operations: authenticate, logout, register, and verify. The
    server uses the registered_users, logged_users, and hasher objects to store
    and validate the user data. The server also logs the relevant messages using
    the logger object.
    """
    server_socket = socket(AF_INET, SOCK_STREAM)
    server_socket.bind(("", IAS_PORT))
    server_socket.listen(IAS_BACKLOG_SIZE)

    logger.log(LogMessage.server_listening(), Logger.INFO)

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
        elif opcode == IasOpCode.LOGOUT:  # args are token and username
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
